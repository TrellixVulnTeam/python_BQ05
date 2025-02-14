# pylint: disable=not-context-manager
'''corr_tests'''
import subprocess
import sys

#third party
import fuckit
import pandas

#My Libs
import funclib.statslib as statslib
import funclib.iolib as iolib
import funclib.stringslib as stringslib

def do_tests():
    '''do tests'''
    pamfile = pandas.read_csv('data\\pam.csv')
    fmmfile = pandas.read_csv('data\\fmm.csv')
    fmmfilenonzero = pandas.read_csv('data\\fmmnonzero.csv')
    pamfilenonzero = pandas.read_csv('data\\pamnonzero.csv')
    assert isinstance(pamfile, pandas.DataFrame)
    assert isinstance(fmmfile, pandas.DataFrame)
    assert isinstance(fmmfilenonzero, pandas.DataFrame)
    assert isinstance(pamfilenonzero, pandas.DataFrame)

    #folder to save results
    outdir = '.\\output\\'

    results = [['test_type', 'desc', 'varname1', 'varname2', 'exclude zeros', 'teststat', 'p', 'n']]
    iterations = stringslib.read_number(raw_input('Input iterations. Enter 0 to not run permutation tests:'), 0)



#region FMM

    #No Zero pairs - VenueCnt vs VALUE
    out = [0]
    dic = statslib.correlation_test_from_csv(fmmfilenonzero, 'VALUE', 'VenueCnt', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'FMM No Zeros', 'VALUE', 'VenueCnt', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = fmmfilenonzero['VenueCnt'].tolist()
        value = fmmfilenonzero['VALUE'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, value, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'fmmNo0_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)

    #ALL - VenueCnt vs VALUE'
    out = [0]
    dic = statslib.correlation_test_from_csv(fmmfile, 'VALUE', 'VenueCnt', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'FMM All data', 'VALUE', 'VenueCnt', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = fmmfile['VenueCnt'].tolist()
        value = fmmfile['VALUE'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, value, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'fmm_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)


    #!!No Zero, Score vs VALUE
    out = [0]
    dic = statslib.correlation_test_from_csv(fmmfilenonzero, 'VALUE', 'Scores', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'FMM No Zeros', 'VALUE', 'Scores', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = fmmfilenonzero['Scores'].tolist()
        value = fmmfilenonzero['VALUE'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, value, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'fmmNo0_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)

    #!!ZEROS - Score vs VALUE'
    out = [0]
    dic = statslib.correlation_test_from_csv(fmmfile, 'VALUE', 'Scores', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'FMM All data', 'VALUE', 'Scores', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = fmmfile['Scores'].tolist()
        value = fmmfile['VALUE'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, value, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'fmm_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)


    #!!No Zero,  VenueCntKM vs VALUE
    out = [0]
    dic = statslib.correlation_test_from_csv(fmmfilenonzero, 'VALUE', 'venueCntKM', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'FMM No Zeros', 'VALUE', 'venueCntKM', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = fmmfilenonzero['venueCntKM'].tolist()
        value = fmmfilenonzero['VALUE'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, value, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'fmmNo0_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)

    #!!ZEROES - VenueCntKM vs VALUE'
    out = [0]
    dic = statslib.correlation_test_from_csv(fmmfile, 'VALUE', 'venueCntKM', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'FMM All data', 'VALUE', 'venueCntKM', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = fmmfile['venueCntKM'].tolist()
        value = fmmfile['VALUE'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, value, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'fmm_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)
#endregion





#region ***PAM***

    #NO ZEROES VenueCnt vs days_pa_km
    out = [0]
    dic = statslib.correlation_test_from_csv(pamfile, 'days_pa_km', 'VenueCnt', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'PAM All data', 'days_pa_km', 'VenueCnt', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = pamfile['VenueCnt'].tolist()
        dayspakm = pamfile['days_pa_km'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, dayspakm, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'pam_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)

    #ZEROES VenueCnt vs days_pa_km
    out = [0]
    dic = statslib.correlation_test_from_csv(pamfilenonzero, 'days_pa_km', 'VenueCnt', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'PAM No Zeros', 'days_pa_km', 'VenueCnt', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = pamfilenonzero['VenueCnt'].tolist()
        dayspakm = pamfilenonzero['days_pa_km'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, dayspakm, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'pamNo0_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)




    #NO ZEROES Scores vs days_pa_km
    out = [0]
    dic = statslib.correlation_test_from_csv(pamfile, 'days_pa_km', 'Scores', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'PAM All data', 'days_pa_km', 'Scores', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = pamfile['Scores'].tolist()
        dayspakm = pamfile['days_pa_km'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, dayspakm, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'pam_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)

    #ZEROES Scores vs days_pa_km
    out = [0]
    dic = statslib.correlation_test_from_csv(pamfilenonzero, 'days_pa_km', 'Scores', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'PAM No Zeros', 'days_pa_km', 'Scores', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = pamfilenonzero['Scores'].tolist()
        dayspakm = pamfilenonzero['days_pa_km'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, dayspakm, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'pamNo0_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)


    #NO ZEROES venueCntKM vs days_pa_km
    out = [0]
    dic = statslib.correlation_test_from_csv(pamfile, 'days_pa_km', 'venueCntKM', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'PAM All data', 'days_pa_km', 'venueCntKM', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = pamfile['venueCntKM'].tolist()
        dayspakm = pamfile['days_pa_km'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, dayspakm, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'pam_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)

    #ZEROES venueCntKM vs days_pa_km
    out = [0]
    dic = statslib.correlation_test_from_csv(pamfilenonzero, 'days_pa_km', 'venueCntKM', statslib.EnumMethod.kendall, statslib.EnumStatsEngine.r)
    results.append(['Kendall', 'PAM No Zeros', 'days_pa_km', 'venueCntKM', 0, dic['teststat'], dic['p'], dic['n']])
    if iterations > 0:
        venuecnt = pamfilenonzero['venueCntKM'].tolist()
        dayspakm = pamfilenonzero['days_pa_km'].tolist()
        corr_results = statslib.permuted_correlation(venuecnt, dayspakm, dic['teststat'], iterations, statslib.EnumMethod.kendall, out)
        file_name = outdir + 'pamNo0_' + stringslib.datetime_stamp() + '.csv'
        iolib.writecsv(file_name, corr_results, inner_as_rows=False)



    #write results to file
    fileout = outdir + 'corr_tests_' + stringslib.datetime_stamp() + '.csv'
    iolib.writecsv(fileout, results, inner_as_rows=False)

    with fuckit:
        subprocess.check_call(['explorer', '.\\output'])
#endregion

do_tests()
sys.exit()
