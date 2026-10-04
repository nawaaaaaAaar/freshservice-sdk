import freshservice
import freshservice.v2


def test_package_imports():
    """
    This test ensures that the package can be imported :0

    """
    assert freshservice.__name__ == "freshservice"
    assert freshservice.v2.__name__ == "freshservice.v2"
