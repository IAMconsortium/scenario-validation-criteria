from pathlib import Path
from shutil import rmtree, copytree


# define main function
def attach_data(setup_kwargs):
    # define source and target paths
    DATA_DIR_SOURCE: Path = Path(__file__).parent.parent / "inst" / "extdata"
    DATA_DIR_TARGET: Path = (
        Path(__file__).parent.parent
        / "python"
        / "scenario_validation_criteria"
        / "data"
    )

    # remove target directory if it exists
    if DATA_DIR_TARGET.exists():
        rmtree(DATA_DIR_TARGET)

    # check if source directory exists
    if not (DATA_DIR_SOURCE.exists() and DATA_DIR_SOURCE.is_dir()):
        raise Exception(
            f"Cannot find data directory for copying: {DATA_DIR_SOURCE}"
        )

    # copy from source to target
    copytree(DATA_DIR_SOURCE, DATA_DIR_TARGET)
    return setup_kwargs


# call main function
if __name__ == "__main__":
    attach_data({})
