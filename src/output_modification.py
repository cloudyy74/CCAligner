import pandas as pd
from numpy import sign


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
        if start_1 > start_2:
            start_1, start_2 = start_2, start_1
            end_1, end_2 = end_2, end_1
        if not (dir1 == dir2 and file_name1 == file_name2 and
                sign(int(start_2) - int(start_1)) * sign(int(start_2) - int(end_1)) < 0):
            filtered_pairs.append([file1, file2])
    return filtered_pairs


def clones_list_to_df(clones_list, lang_ext):
    clones_df = pd.DataFrame({'dir1': pd.Series(dtype='str'),
                              'name1': pd.Series(dtype='str'),
                              'start1': pd.Series(dtype='int'),
                              'end1': pd.Series(dtype='int'),
                              'dir2': pd.Series(dtype='str'),
                              'name2': pd.Series(dtype='str'),
                              'start2': pd.Series(dtype='int'),
                              'end2': pd.Series(dtype='int'),
                              })
    list_with_records = list()
    for file1, file2 in clones_list:  # writes list of clones into the dataframe
        dir1 = file1.split('/')[-3]
        dir2 = file2.split('/')[-3]
        file_name1 = file1.split('/')[-2] + lang_ext
        file_name2 = file2.split('/')[-2] + lang_ext
        start_1, end_1 = file1.split('/')[-1][:-len(lang_ext)].split('_')
        start_2, end_2 = file2.split('/')[-1][:-len(lang_ext)].split('_')
        list_with_records.append([dir1, file_name1, start_1, end_1, dir2, file_name2, start_2,
                                  end_2])
    return pd.concat([clones_df, pd.DataFrame(list_with_records, columns=['dir1', 'name1', 'start1', 'end1',
                                                                          'dir2', 'name2', 'start2', 'end2'])],
                     ignore_index=True)


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



def sort_clones(df):
    """
    first sorting by the name of file of first fragment, then by the name of file of second fragment
    :param df:
    :return:
    """
    df.sort_values(by=['name1', 'name2'], inplace=True)