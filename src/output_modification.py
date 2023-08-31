import pandas as pd

column_names = dict(dir1=pd.Series(dtype='str'), name1=pd.Series(dtype='str'), start1=pd.Series(dtype='int'),
                    end1=pd.Series(dtype='int'), dir2=pd.Series(dtype='str'), name2=pd.Series(dtype='str'),
                    start2=pd.Series(dtype='int'), end2=pd.Series(dtype='int'))


def filter_nested_clones(pairs, lang_ext):
    """
    filters pairs, where one of the fragment is in the second one
    :param pairs:
    :return:
    """
    filtered_pairs = list()
    for file1, file2 in pairs:  # filters nested clones
        file1_info = file1.split('/')
        file2_info = file2.split('/')
        dir1 = file1_info[-3]
        dir2 = file2_info[-3]
        file_name1 = file1_info[-2] + lang_ext
        file_name2 = file2_info[-2] + lang_ext
        start_1, end_1 = file1_info[-1][:-len(lang_ext)].split('_')
        start_2, end_2 = file2_info[-1][:-len(lang_ext)].split('_')
        if not (dir1 == dir2 and file_name1 == file_name2 and
                (int(start_2) in range(int(start_1), int(end_1)) or int(start_1) in range(int(start_2), int(end_2)))):
            filtered_pairs.append([file1, file2])
    return filtered_pairs


def to_benchmark_format(fragment_name, lang_ext):
    dir = fragment_name.split('/')[-3]
    file_name = fragment_name.split('/')[-2] + lang_ext
    start, end = fragment_name.split('/')[-1][:-len(lang_ext)].split('_')
    return [dir, file_name, start, end]


def clones_list_to_df(clones_list, lang_ext):
    clones_df = pd.DataFrame(column_names)
    list_with_records = list()
    for file1, file2 in clones_list:
        dir1 = file1.split('/')[-3]
        dir2 = file2.split('/')[-3]
        file_name1 = file1.split('/')[-2] + lang_ext
        file_name2 = file2.split('/')[-2] + lang_ext
        start_1, end_1 = file1.split('/')[-1][:-len(lang_ext)].split('_')
        start_2, end_2 = file2.split('/')[-1][:-len(lang_ext)].split('_')
        list_with_records.append([dir2, file_name2, start_2, end_2,
                                  dir1, file_name1, start_1, end_1])
    return pd.concat([clones_df, pd.DataFrame(list_with_records, columns=['dir1', 'name1', 'start1', 'end1',
                                                                          'dir2', 'name2', 'start2', 'end2'])],
                     ignore_index=True).drop_duplicates()


def list_record_to_benchmark_record(pair, lang_ext):
    first_fragment = ','.join(to_benchmark_format(pair[0], lang_ext))
    second_fragment = ','.join(to_benchmark_format(pair[1], lang_ext))
    return ','.join([first_fragment, second_fragment])


def write_clone_list(clones_list, lang_ext, file_output):
    with open(file_output, 'w+') as f:
        f.writelines(list_record_to_benchmark_record(rec, lang_ext) + '\n' for rec in clones_list)
    return True


def regulate_records(df):
    """
    regulate dataframe with clones to next format:
    first fragment is longer, if same length, first is that fragment, that begins earlier.
    then drops duplicates
    :param df:
    :return df:
    """
    for i in range(len(df)):
        length1 = int(df.loc[i, 'end1']) - int(df.loc[i, 'start1'])
        length2 = int(df.loc[i, 'end2']) - int(df.loc[i, 'start2'])
        if length1 < length2 or (length1 == length2 and df.loc[i, 'start1'] > df.loc[i, 'start2']):
            df.loc[i, 'start1'], df.loc[i, 'start2'] = df.loc[i, 'start2'], df.loc[i, 'start1']
            df.loc[i, 'end1'], df.loc[i, 'end2'] = df.loc[i, 'end2'], df.loc[i, 'end1']
            df.loc[i, 'dir1'], df.loc[i, 'dir2'] = df.loc[i, 'dir2'], df.loc[i, 'dir1']
            df.loc[i, 'name1'], df.loc[i, 'name2'] = df.loc[i, 'name2'], df.loc[i, 'name1']
    return df.drop_duplicates()


def fragments_consisting_this(df, row):
    filtration_names = (df['dir1'] == row['dir1']) & (df['dir2'] == row['dir2']) & \
                       (df['name1'] == row['name1']) & (df['name2'] == row['name2'])
    first_consisting = (df['start1'] <= row['start1']) & (df['end1'] >= row['end1'])
    second_consisting = (df['start2'] <= row['start2']) & (df['end2'] >= row['end2'])
    return df[filtration_names & first_consisting & second_consisting]


def only_biggest(df):
    biggest_fragments = pd.DataFrame(column_names)
    for index, row in df.iterrows():
        if len(fragments_consisting_this(df, row)) == 1:
            biggest_fragments.loc[len(biggest_fragments)] = row

    return biggest_fragments


def sort_clones(df):
    """
    first sorting by the name of file of first fragment, then by the name of file of second fragment
    :param df:
    :return:
    """
    df.sort_values(by=['name1', 'name2', 'start1', 'start2'], inplace=True)


def different_files(df):
    mask = (df['name1'] != df['name2'])
    return df[mask]


def suspicious_hws(df):
    df2 = df[['name1', 'name2']]
    return df2.drop_duplicates()
