import logging
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def print_number(lowest: int, highest: int) -> dict[str, Any]:
    """
    Print numbers in a given range from lowest to highest.

    This function is designed to be executed as a background job in Redis Queue.
    It logs progress and returns a summary of the job execution.

    Args:
        lowest: The starting number (inclusive)
        highest: The ending number (inclusive)

    Returns:
        Dictionary containing job execution summary

    Raises:
        ValueError: If lowest is greater than highest
        TypeError: If inputs are not integers
    """
    # Input validation
    if not isinstance(lowest, int) or not isinstance(highest, int):
        error_msg = f"Both arguments must be integers. Got lowest={type(lowest)}, highest={type(highest)}"
        logger.error(error_msg)
        raise TypeError(error_msg)

    if lowest > highest:
        error_msg = f"lowest ({lowest}) cannot be greater than highest ({highest})"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Job processing started: printing numbers from {lowest} to {highest}")

    count = 0
    try:
        for number in range(lowest, highest + 1):
            print(number)
            count += 1

            # Log progress for long-running jobs (every 1000 numbers)
            if count % 1000 == 0:
                logger.info(f"Progress: {count} numbers printed so far")

        logger.info(f"Job completed successfully. Printed {count} numbers.")

        return {
            "status": "completed",
            "lowest": lowest,
            "highest": highest,
            "total_numbers": count,
            "message": f"Successfully printed {count} numbers from {lowest} to {highest}",
        }

    except Exception as e:
        error_msg = f"Job failed with error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise
