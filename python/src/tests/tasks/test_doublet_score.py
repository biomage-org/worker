import pytest
import anndata
import os
import statistics
from tasks.doublet_score import GetDoubletScore
import json
from config import get_config
import responses

config = get_config()


class TestGetDoubletScore:
    @pytest.fixture(autouse=True)
    def load_correct_definition(self):
        self.correct_request = {
            "experimentId": "5e959f9c9f4b120771249001",
            "timeout": "2099-12-31 00:00:00",
            "body": {
                "name": "getDoubletScore",
                "cells": ["0", "1"],
            },
        }

    @pytest.fixture(autouse=True)
    def set_responses(self):
        with open(os.path.join("tests", "DoubletScore_result.json")) as f:
            data = json.load(f)
            responses.add(
                responses.POST,
                f"{config.R_WORKER_URL}/v0/getDoubletScore",
                json=data,
                status=200,
            )

    def test_throws_on_missing_parameters(self):
        with pytest.raises(TypeError):
            GetDoubletScore()

    def test_works_with_request(self):
        GetDoubletScore(self.correct_request)

    @responses.activate
    def test_returns_json(self):
        res = GetDoubletScore(self.correct_request).compute()
        res = res[0].result
        json.loads(res)

    @responses.activate
    def test_returns_a_json_object(self):
        res = GetDoubletScore(self.correct_request).compute()
        res = res[0].result
        res = json.loads(res)
        assert isinstance(res, dict)

    @responses.activate
    def test_object_returns_appropriate_number_of_cells(self):
        res = GetDoubletScore(self.correct_request).compute()
        res = res[0].result
        res = json.loads(res)
        assert len(res) == len(self.correct_request["body"]["cells"])