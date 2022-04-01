import json

import backoff
# import pandas as pd
import requests
from aws_xray_sdk.core import xray_recorder
from exceptions import raise_if_error

from ..config import config
from ..helpers.color_pool import COLOR_POOL
from ..result import Result
from ..tasks import Task

# from logging import info
# from natsort import natsorted


class ClusterCells(Task):
    def __init__(self, msg):
        super().__init__(msg)
        self.colors = COLOR_POOL.copy()
        self.request = msg

    # def _convert_to_cell_set_object(self, raw):
    #     # construct new cell set group
    #     cell_set_key = self.task_def["cellSetKey"]
    #     cell_set_name = self.task_def["cellSetName"]

    #     cell_set = {
    #         "key": cell_set_key,
    #         "name": cell_set_name,
    #         "rootNode": True,
    #         "type": "cellSets",
    #         "children": [],
    #     }

    #     for cluster in natsorted(raw["cluster"].cat.categories):
    #         view = raw[raw.cluster == cluster]["cell_ids"]
    #         cell_set["children"].append(
    #             {
    #                 "key": f"{cell_set_key}-{cluster}",
    #                 "name": f"Cluster {cluster}",
    #                 "rootNode": False,
    #                 "type": "cellSets",
    #                 "color": self.colors.pop(0),
    #                 "cellIds": list(view.map(int)),
    #             }
    #         )

    #     return cell_set

    # def _update_through_api(self, cell_set_object):
    #     r = requests.patch(
    #         f"{config.API_URL}/v1/experiments/{self.request['experimentId']}/cellSets",
    #         headers={
    #             "content-type": "application/boschni-json-merger+json",
    #             "Authorization": self.request["Authorization"],
    #         },
    #         json=[
    #             {
    #                 "$match": {
    #                     "query": f'$[?(@.key == "{self.task_def["cellSetKey"]}")]',
    #                     "$remove": True,
    #                 },
    #             },
    #             {
    #                 "$prepend": cell_set_object,
    #             },
    #         ],
    #     )

    #     info(r.status_code)

    def _format_result(self, result):
        return Result(result, cacheable=False)

    def _format_request(self):
        resolution = self.task_def["config"].get("resolution", 0.5)
        config = self.task_def.get("config", {"resolution": resolution})

        patch_config = {
            "experimentId": config.EXPERIMENT_ID,
            "apiUrl": config.API_URL,
            "authJwt": self.request["Authorization"],
        }

        request = {
            "type": self.task_def["type"],
            "config": {**config, **patch_config}
        }

        return request

    @xray_recorder.capture("ClusterCells.compute")
    @backoff.on_exception(
        backoff.expo, requests.exceptions.RequestException, max_time=30
    )
    def compute(self):

        request = self._format_request()

        response = requests.post(
            f"{config.R_WORKER_URL}/v0/getClusters",
            headers={"content-type": "application/json"},
            data=json.dumps(request),
        )

        response.raise_for_status()
        result = response.json()
        raise_if_error(result)

        data = result.get("data")

        # This is a questionable bit of code, but basically it was a simple way of adjusting the results to the shape
        # expected by the UI Doing this allowed me to use the format function as is. It shouldn't be too taxing,
        # at most O(n of cells), which is well within our time complexity because the taxing part will be clustering.
        # df = pd.DataFrame(data)
        # df.set_index("_row", inplace=True)
        # df["cluster"] = pd.Categorical(df.cluster)

        # Convert it into a JSON format and patch the API directly
        # cell_set_object = self._convert_to_cell_set_object(df)
        # self._update_through_api(cell_set_object)

        return self._format_result(data)
