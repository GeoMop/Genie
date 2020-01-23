import pandas as pd


def parse(file_name):
    ret = {"warnings": [],
           "errors": [],
           "header": {},
           "data": None}

    with open(file_name) as fd:
        # read header
        while True:
            line = fd.readline()
            if ":" in line:
                sp = line.split(":", maxsplit=1)
                ret["header"][sp[0]] = sp[1].strip()
            else:
                break

        fd.readline()

        raw_df = pd.read_csv(fd, header=None, sep="\t")
        # remove last empty column
        raw_df = raw_df.dropna(axis=1)
        # name columns
        raw_df.columns = ['ca', 'cb', 'pa', 'pb', 'array', 'I', 'V', 'EP', 'AppRes', 'std']

        # remove wrong readings
        raw_df = raw_df.drop(raw_df[raw_df['V'] < 0].index)

        # input error is in percent
        raw_df['std'] *= 0.01

        # mV -> V, mA -> A
        raw_df['I'] *= 0.001
        raw_df['V'] *= 0.001
        raw_df['EP'] *= 0.001

        ret["data"] = raw_df

    return ret
