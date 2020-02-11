import pandas as pd


def parse(file_name):
    with open(file_name) as fd:
        line = fd.readline()
    if line.startswith("Device: ARES II"):
        return _parse_ares2(file_name)
    return _parse_ares(file_name)


def _parse_ares(file_name):
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


def _parse_ares2(file_name):
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

        raw_df = pd.read_csv(fd, header=None, sep="\t")
        # name columns
        raw_df.columns = ['ca', 'cb', 'pa', 'pb', 'Pn', 'Pn_1', 'array', 'Uout', 'I', 'V', 'EP', 'AppRes', 'std']

        # remove wrong readings
        raw_df = raw_df.drop(raw_df[raw_df['V'] < 0].index)

        # input error is in percent
        raw_df['std'] *= 0.01

        # mV -> V, mA -> A
        raw_df['I'] *= 0.001
        raw_df['V'] *= 0.001
        raw_df['EP'] *= 0.001

        # remove * from ca, cb
        def rem_star(x):
            if isinstance(x, str):
                s = x.split("*", maxsplit=1)
                return int(s[0])
            return x

        raw_df['ca'] = raw_df['ca'].apply(rem_star)
        raw_df['cb'] = raw_df['cb'].apply(rem_star)

        ret["data"] = raw_df

    return ret
