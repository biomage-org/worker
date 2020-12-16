import pytest
import anndata
import os
from tasks.differential_expression import DifferentialExpression
import json
from botocore.stub import Stubber
import mock
import boto3
import responses
from config import get_config
from boto3.dynamodb.types import TypeSerializer

config = get_config()


class TestDifferentialExpression:
    @pytest.fixture(autouse=True)
    def open_test_adata(self):
        self._adata = anndata.read_h5ad(
            os.path.join(config.LOCAL_DIR, "test", "python.h5ad")
        )

    @pytest.fixture(autouse=True)
    def load_correct_definition(self):
        self.correct_request = {
            "experimentId": "5e959f9c9f4b120771249001",
            "timeout": "2099-12-31 00:00:00",
            "body": {
                "name": "DifferentialExpression",
                "cellSet": "cluster1",
                "compareWith": "rest",
            },
        }

        with open(os.path.join("tests", "de_result.json")) as f:
            data = json.load(f)
            responses.add(
                responses.POST,
                f"{config.R_WORKER_URL}/v0/DifferentialExpression",
                json=data,
                status=200,
            )

    """
    Mocks the DynamoDB query for fetching cell sets. Returns an
    empty cell set and yields the patched up object.
    """

    @pytest.fixture
    def mock_dynamo_get(self):
        ser = TypeSerializer()

        response = [
            {"name": "my amazing cluster", "key": "cluster1", "cellIds": [4, 5]},
            {
                "name": "my other amazing cluster",
                "key": "cluster2",
                "cellIds": [0, 1, 2, 3],
            },
        ]

        response = ser.serialize(response)

        test_experiment_id = self.correct_request["experimentId"]

        dynamodb = boto3.resource("dynamodb", **config.BOTO_RESOURCE_KWARGS)
        stubber = Stubber(dynamodb.meta.client)
        stubber.add_response(
            "get_item",
            {"Item": {"cellSets": response}},
            {
                "TableName": config.DYNAMO_TABLE,
                "Key": {"experimentId": test_experiment_id},
                "ProjectionExpression": "cellSets",
            },
        )
        stubber.activate()

        with mock.patch("boto3.resource") as m:
            yield (m, dynamodb)

    @responses.activate
    def test_throws_on_missing_parameters(self):
        with pytest.raises(TypeError):
            DifferentialExpression()

    @responses.activate
    def test_throws_on_missing_adata(self):
        with pytest.raises(TypeError):
            DifferentialExpression(self.correct_request)

    @responses.activate
    def test_dynamodb_call_is_made_once_when_vs_rest(self):
        with mock.patch("boto3.resource") as m:
            global no_called
            no_called = 0

            class MockTable:
                def get_item(*args, **kwargs):
                    global no_called

                    no_called += 1

                    response = [
                        {
                            "name": "my amazing cluster",
                            "key": "cluster1",
                            "cellIds": [4, 5],
                        },
                        {
                            "name": "my other amazing cluster",
                            "key": "cluster2",
                            "cellIds": [0, 1, 2, 3],
                        },
                    ]

                    # response = ser.serialize(response)

                    return {"Item": {"cellSets": response}}

            class MockDynamoClass:
                def Table(*args, **kwargs):
                    return MockTable()

            m.return_value = MockDynamoClass()
            DifferentialExpression(self.correct_request, self._adata).compute()

            assert no_called == 1

    @responses.activate
    def test_cell_sets_get_queried_appropriately(self, mock_dynamo_get):
        m, dynamodb = mock_dynamo_get
        m.return_value = dynamodb
        DifferentialExpression(self.correct_request, self._adata).compute()

    @responses.activate
    def test_works_with_request_and_adata(self, mock_dynamo_get):
        m, dynamodb = mock_dynamo_get
        m.return_value = dynamodb
        DifferentialExpression(self.correct_request, self._adata)

    @responses.activate
    def test_works_when_rest_is_first(self, mock_dynamo_get):
        m, dynamodb = mock_dynamo_get
        m.return_value = dynamodb

        self.correct_request["cellSet"] = "rest"
        self.correct_request["compareWith"] = "cluster1"

        DifferentialExpression(self.correct_request, self._adata)

    @responses.activate
    def test_works_when_all_is_first(self, mock_dynamo_get):
        m, dynamodb = mock_dynamo_get
        m.return_value = dynamodb

        self.correct_request["cellSet"] = "all-asdasd"
        self.correct_request["compareWith"] = "cluster1"
        
        DifferentialExpression(self.correct_request, self._adata)

    @responses.activate
    def test_returns_json(self, mock_dynamo_get):
        m, dynamodb = mock_dynamo_get
        m.return_value = dynamodb

        res = DifferentialExpression(self.correct_request, self._adata).compute()
        res = res[0].result
        json.loads(res)

    @responses.activate
    def test_returns_a_json_object(self, mock_dynamo_get):
        m, dynamodb = mock_dynamo_get
        m.return_value = dynamodb

        res = DifferentialExpression(self.correct_request, self._adata).compute()
        res = res[0].result
        res = json.loads(res)
        assert isinstance(res, dict)

    @responses.activate
    def test_object_has_all_required_columns(self, mock_dynamo_get):
        m, dynamodb = mock_dynamo_get
        m.return_value = dynamodb

        res = DifferentialExpression(self.correct_request, self._adata).compute()
        res = res[0].result
        res = json.loads(res)

        for row in res["rows"]:
            keys = sorted(row.keys())
            expected_keys = sorted(["gene_names", "zscore", "abszscore", "qval", "log2fc", "_row"])
            assert keys == expected_keys

    @responses.activate
    def test_appropriate_genes_returned_when_a_limit_is_specified(
        self, mock_dynamo_get
    ):
        m, dynamodb = mock_dynamo_get
        m.return_value = dynamodb

        request = self.correct_request
        request["body"]["maxNum"] = 2

        res = DifferentialExpression(request, self._adata).compute()
        res = res[0].result
        res = json.loads(res)["rows"]

        assert len(res) <= request["body"]["maxNum"]

    @responses.activate
    def test_all_genes_returned_when_no_limit_is_specified(self, mock_dynamo_get):
        m, dynamodb = mock_dynamo_get
        m.return_value = dynamodb

        res = DifferentialExpression(self.correct_request, self._adata).compute()
        res = res[0].result
        res = json.loads(res)["rows"]

        assert len(res) <= len(self._adata.raw.var.index)