import geopandas as gpd
import numpy as np
from .microcensusConstants import *


# called in 01
def impute_sp_region(df):
    SP_REGION_1 = [25, 12, 13, 1, 2, 14, 9]
    SP_REGION_2 = [21, 26, 15, 16, 22, 11, 24, 3, 6, 7]
    SP_REGION_3 = [17, 19, 10, 23, 20, 5, 18, 4, 8]

    assert ("canton_id" in df.columns)
    assert ("sp_region" not in df.columns)

    df["sp_region"] = 0
    df.loc[df["canton_id"].isin(SP_REGION_1), "sp_region"] = 1
    df.loc[df["canton_id"].isin(SP_REGION_2), "sp_region"] = 2
    df.loc[df["canton_id"].isin(SP_REGION_3), "sp_region"] = 3

    # TODO: There are some municipalities that are not included in the shape
    # file above. Hence, they get region 0. Should be fixed in the future.
    # Especially, we need a consistent spatial system. It probably would make
    # more sense to impute the SP region in another way

    # assert(not np.any(df["sp_region"] == 0))
    return df
    

# called in 01
def assign_household_class(df):
    """
        Combines all houeshold sizes above 5 into one class.

        Attention! Here KM also says that houesholds with at least one married person
        have a minimum size of 2. Technically, this doesn't need be true in reality, and
        I'm not sure if it has any implications later on. (TODO)
    """
    df["household_size_class"] = np.minimum(5, df["household_size"]) - 1

# called in 01
def fix_marital_status(df):
    """ Makes young people, who are separated, be treated as single! """
    df.loc[
        (df["marital_status"] == MARITAL_STATUS_SEPARATE) & (df["age"] < SEPARATE_SINGLE_THRESHOLD)
        , "marital_status"] = MARITAL_STATUS_SINGLE
    df.loc[:, "marital_status"] = df.loc[:, "marital_status"].astype(int)
