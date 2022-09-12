"""
The main function to start the transformation
"""
from transform_jao2eds.transform import TransformJao2Eds


def main():
    """
    The main function which runs the transformation.
    """
    transform = TransformJao2Eds()

    transform.transform()


if __name__ == '__main__':
    main()
