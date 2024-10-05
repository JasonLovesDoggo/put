import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from main import app
from server.storages.base import AbstractStorage
from server.metadata import FileMetadata


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_storage():
    return Mock(spec=AbstractStorage)


def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_verify_signature(test_client):
    response = test_client.put("/signature")
    assert response.status_code == 200
    assert "version" in response.json()
    assert "verifier" in response.json()
    assert "compatible_versions" in response.json()


@pytest.mark.asyncio
async def test_list_files(mock_storage):
    mock_storage.list.return_value = [
        {"name": "file1.txt", "size": 1000},
        {"name": "file2.txt", "size": 2000},
    ]

    with patch("main.create_storage", return_value=mock_storage):
        response = await app.get("/api/list")
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["name"] == "file1.txt"


@pytest.mark.asyncio
async def test_delete_file(mock_storage):
    with patch("main.create_storage", return_value=mock_storage):
        response = await app.delete("/api/file123")
        assert response.status_code == 204
        mock_storage.delete.assert_called_once_with("file123")


@pytest.mark.asyncio
async def test_delete_file_not_found(mock_storage):
    mock_storage.delete.side_effect = FileNotFoundError()

    with patch("main.create_storage", return_value=mock_storage):
        response = await app.delete("/api/file123")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_file(mock_storage):
    mock_file = Mock()
    mock_file.name = "test.txt"
    mock_file.size = 1000
    mock_storage.get.return_value = mock_file

    with patch("main.create_storage", return_value=mock_storage):
        response = await app.get("/api/file123")
        assert response.status_code == 200
        assert response.json()["name"] == "test.txt"
        assert response.json()["size"] == 1000


@pytest.mark.asyncio
async def test_create_upload(test_client, mock_storage):
    mock_metadata = FileMetadata(  # noqa: F841
        uid="test123",
        metadata={"filename": "test.txt", "filetype": "text/plain"},
        size=1000,
        created_at="2023-01-01T00:00:00",
        defer_length=False,
        expires="2023-01-06T00:00:00",
    )

    with patch("tus._write_metadata") as mock_write_metadata, patch(
        "tus._initialize_file"
    ) as mock_initialize_file, patch("main.create_storage", return_value=mock_storage):
        response = test_client.post(
            "/files",
            headers={
                "Upload-Metadata": "filename dGVzdC50eHQ=, filetype dGV4dC9wbGFpbg==",
                "Upload-Length": "1000",
            },
        )

        assert response.status_code == 201
        assert "Location" in response.headers
        mock_write_metadata.assert_called_once()
        mock_initialize_file.assert_called_once()


@pytest.mark.asyncio
async def test_upload_chunk(test_client, mock_storage):
    mock_metadata = FileMetadata(
        uid="test123",
        metadata={"filename": "test.txt", "filetype": "text/plain"},
        size=1000,
        offset=500,
        created_at="2023-01-01T00:00:00",
        defer_length=False,
        expires="2023-01-06T00:00:00",
    )

    with patch("tus._read_metadata", return_value=mock_metadata), patch(
        "tus._file_exists", return_value=True
    ), patch("tus._write_metadata") as mock_write_metadata, patch(
        "main.create_storage", return_value=mock_storage
    ):
        response = test_client.patch(
            "/files/test123",
            headers={
                "Content-Type": "application/offset+octet-stream",
                "Upload-Offset": "500",
                "Content-Length": "500",
            },
            data="0" * 500,
        )

        assert response.status_code == 204
        assert "Upload-Offset" in response.headers
        assert response.headers["Upload-Offset"] == "1000"
        mock_write_metadata.assert_called_once()


# Add more tests for edge cases, error handling, and other scenarios
