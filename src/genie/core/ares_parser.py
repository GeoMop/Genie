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

        raw_df = pd.read_csv(fd, header=None, sep="\t", index_col=False, engine="python")
        # remove last empty column
        raw_df = raw_df.dropna(axis=1)
        # name columns
        raw_df.columns = ['ca', 'cb', 'pa', 'pb', 'array', 'I', 'V', 'EP', 'AppRes', 'std']

        # remove wrong readings
        #raw_df = raw_df.drop(raw_df[raw_df['V'] < 0].index)

        # input error is in percent
        raw_df['std'] *= 0.01

        # mV -> V, mA -> A
        raw_df['I'] *= 0.001
        raw_df['V'] *= 0.001
        raw_df['EP'] *= 0.001

        # change type
        raw_df['AppRes'] = raw_df['AppRes'].astype('float64')

        raw_df['ca'] = raw_df['ca'].apply(lambda x: str(x))
        raw_df['cb'] = raw_df['cb'].apply(lambda x: str(x))
        raw_df['pa'] = raw_df['pa'].apply(lambda x: str(x))
        raw_df['pb'] = raw_df['pb'].apply(lambda x: str(x))

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

        # name columns
        names = ['ca', 'cb', 'pa', 'pb', 'Pn', 'Pn_1', 'array', 'Uout', 'I', 'V', 'EP', 'AppRes', 'std']

        raw_df = pd.read_csv(fd, header=None, sep="\t", names=names, index_col=False, engine="python")

        # remove wrong readings
        #raw_df = raw_df.drop(raw_df[raw_df['V'] < 0].index)

        # input error is in percent
        raw_df['std'] *= 0.01

        # mV -> V, mA -> A
        raw_df['I'] *= 0.001
        raw_df['V'] *= 0.001
        raw_df['EP'] *= 0.001

        # change type
        raw_df['AppRes'] = raw_df['AppRes'].astype('float64')

        # remove * from ca, cb
        def rem_star(x):
            if isinstance(x, str):
                s = x.split("*", maxsplit=1)
                return s[0]
            return str(x)

        raw_df['ca'] = raw_df['ca'].apply(rem_star)
        raw_df['cb'] = raw_df['cb'].apply(rem_star)
        raw_df['pa'] = raw_df['pa'].apply(lambda x: str(x))
        raw_df['pb'] = raw_df['pb'].apply(lambda x: str(x))

        ret["data"] = raw_df

    return ret
