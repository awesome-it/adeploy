import logging
from argparse import Namespace

import adeploy.main  # noqa: F401 - initializes package imports in CLI order.
import pytest

from adeploy.common.errors import RenderError
from adeploy.common.provider import Provider


class DummyProvider(Provider):
    def parse_args(self, args: dict):
        return None


def make_args(**overrides):
    values = {
        "filters_namespace": None,
        "filters_release": None,
        "show_configs": False,
        "force": False,
    }
    values.update(overrides)
    return Namespace(**values)


def patch_kubectl(monkeypatch):
    monkeypatch.setattr(
        "adeploy.common.provider.kubectl_get_current_api_server_url", lambda log: None
    )


def make_provider(project_dir, name="app"):
    return DummyProvider(
        name=name,
        src_dir=project_dir,
        build_dir=project_dir / "build",
        namespaces_dir="namespaces",
        defaults_paths=["defaults.yml"],
        args=make_args(),
        log=logging.getLogger("tests"),
    )


def test_loads_legacy_release_file(tmp_path, monkeypatch):
    patch_kubectl(monkeypatch)
    (tmp_path / "defaults.yml").write_text("image: nginx\n")
    namespace_dir = tmp_path / "namespaces" / "playground"
    namespace_dir.mkdir(parents=True)
    (namespace_dir / "prod.yml").write_text("replicas: 2\n")

    deployments = make_provider(tmp_path).load_deployments()

    assert [(d.namespace, d.release) for d in deployments] == [("playground", "prod")]
    assert deployments[0].config == {"image": "nginx", "replicas": 2}


def test_loads_release_directory_fragments_in_order(tmp_path, monkeypatch):
    patch_kubectl(monkeypatch)
    (tmp_path / "defaults.yml").write_text("image: nginx\n")
    release_dir = tmp_path / "namespaces" / "playground" / "prod"
    release_dir.mkdir(parents=True)
    (release_dir / "000-common.yml").write_text("service:\n  name: api\n")
    (release_dir / "010-app.yml").write_text(
        "service:\n  url: https://{{ service.name }}.example.test\n"
    )

    deployments = make_provider(tmp_path).load_deployments()

    assert [(d.namespace, d.release) for d in deployments] == [("playground", "prod")]
    assert deployments[0].config == {
        "image": "nginx",
        "service": {
            "name": "api",
            "url": "https://api.example.test",
        },
    }


def test_rejects_legacy_file_and_release_directory_for_same_release(
    tmp_path, monkeypatch
):
    patch_kubectl(monkeypatch)
    (tmp_path / "defaults.yml").write_text("image: nginx\n")
    namespace_dir = tmp_path / "namespaces" / "playground"
    namespace_dir.mkdir(parents=True)
    (namespace_dir / "prod.yml").write_text("replicas: 2\n")
    release_dir = namespace_dir / "prod"
    release_dir.mkdir()
    (release_dir / "000-common.yml").write_text("replicas: 3\n")

    with pytest.raises(RenderError, match="defined more than once"):
        make_provider(tmp_path).load_deployments()
