import numpy as np
import pandas as pd

import constants as c


def fix_marital_status(df):
    """ Makes young people, who are separated, be treated as single! """
    df.loc[
        (df["marital_status"] == c.MARITAL_STATUS_SEPARATE) & (df["age"] < c.SEPARATE_SINGLE_THRESHOLD)
        , "marital_status"] = c.MARITAL_STATUS_SINGLE
    df.loc[:, "marital_status"] = df.loc[:, "marital_status"].astype(np.int)





def read_csv(context, fp, fields, renames=None, sep=";", total=None, encoding="latin1", limit=None):
    if renames is None:
        renames = {}
    header = None
    data = []

    count = 0

    for line in context.progress(fp, total=total):
        line = line.decode(encoding).strip().split(sep)

        if header is None:
            header = line
        else:
            data.append([
                field_function(line[header.index(field_name)])
                for field_name, field_function in fields.items()
            ])

        count += 1

        if limit is not None and count == limit:
            break

    columns = [
        renames[field_name] if field_name in renames else field_name
        for field_name in fields.keys()
    ]

    return pd.DataFrame.from_records(data, columns=columns)
