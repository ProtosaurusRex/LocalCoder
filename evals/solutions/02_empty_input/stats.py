def average(nums):
    """Return the mean of nums. An empty list averages to 0.0."""
    if not nums:
        return 0.0
    return sum(nums) / len(nums)
