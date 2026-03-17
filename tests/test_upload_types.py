"""
媒体上传类型测试
"""

import pytest
from wecom_aibot.types import (
    WeComMediaType,
    VideoOptions,
    UploadMediaOptions,
    UploadMediaFinishResult,
)
from wecom_aibot.exceptions import (
    UploadError,
    UploadInitError,
    UploadFinishError,
    ChunkUploadError,
)


class TestVideoOptions:
    """VideoOptions 测试"""

    def test_create_with_all_fields(self):
        """测试创建带所有字段的实例"""
        options = VideoOptions(title="测试视频", description="这是一个测试")
        assert options.title == "测试视频"
        assert options.description == "这是一个测试"

    def test_create_with_defaults(self):
        """测试使用默认值创建"""
        options = VideoOptions()
        assert options.title is None
        assert options.description is None


class TestUploadMediaOptions:
    """UploadMediaOptions 测试"""

    def test_create_valid_options(self):
        """测试创建有效的上传选项"""
        options = UploadMediaOptions(type="image", filename="test.png")
        assert options.type == "image"
        assert options.filename == "test.png"

    def test_validation_empty_filename(self):
        """测试空文件名验证"""
        with pytest.raises(ValueError, match="filename 不能为空"):
            UploadMediaOptions(type="image", filename="")

    def test_validation_whitespace_filename(self):
        """测试空白文件名验证"""
        with pytest.raises(ValueError, match="filename 不能为空"):
            UploadMediaOptions(type="image", filename="   ")

    def test_validation_invalid_type(self):
        """测试无效类型验证"""
        with pytest.raises(ValueError, match="type 必须是"):
            UploadMediaOptions(type="invalid", filename="test.png")

    @pytest.mark.parametrize("media_type", ["file", "image", "voice", "video"])
    def test_all_valid_types(self, media_type: str):
        """测试所有有效媒体类型"""
        options = UploadMediaOptions(type=media_type, filename="test.dat")
        assert options.type == media_type


class TestUploadMediaFinishResult:
    """UploadMediaFinishResult 测试"""

    def test_from_response(self):
        """测试从响应创建实例"""
        body = {
            "type": "image",
            "media_id": "abc123",
            "created_at": "2024-01-01T00:00:00Z",
        }
        result = UploadMediaFinishResult.from_response(body)
        assert result.type == "image"
        assert result.media_id == "abc123"
        assert result.created_at == "2024-01-01T00:00:00Z"


class TestExceptions:
    """异常类型测试"""

    def test_upload_error_is_exception(self):
        """测试 UploadError 是 Exception 子类"""
        assert issubclass(UploadError, Exception)

    def test_upload_init_error_is_upload_error(self):
        """测试 UploadInitError 继承关系"""
        assert issubclass(UploadInitError, UploadError)

    def test_upload_finish_error_is_upload_error(self):
        """测试 UploadFinishError 继承关系"""
        assert issubclass(UploadFinishError, UploadError)

    def test_chunk_upload_error_attributes(self):
        """测试 ChunkUploadError 属性"""
        error = ChunkUploadError(chunk_index=5, attempts=3, message="Network error")
        assert error.chunk_index == 5
        assert error.attempts == 3
        assert "Chunk 5 failed after 3 attempts: Network error" in str(error)
