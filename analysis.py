import collections
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# On 17/07/2021
# To get absolute value (in PLN), multiply by this
CURRENCY_EXCHANGE = {
    "Polska": 1.,
    "Kalifornia, Stany Zjednoczone Ameryki": 3.88,
    "Stan Waszyngton, Stany Zjednoczone Ameryki": 3.88,
    "Stan Nowy Jork, Stany Zjednoczone Ameryki": 3.88,
    "Inny stan, Stany Zjednoczone Ameryki": 3.88,
    "USA": 3.88,
    "Szwajcaria": 4.22,
    "Francja": 4.58,
    "Belgia": 4.58,
    "Niemcy": 4.58,
    "Czechy": 0.18,
    "Wielka Brytania": 5.35,
    "Dania": 1.62,
    "Azja (waluta USD)": 3.88,
    "Szwecja": 0.152055,
    "Austria": 4.58,
    "Hiszpania": 4.58,
    "Holandia": 4.58,
    "Irlandia": 4.58,
    "wietnam": 0.00017,
}

# https://data.oecd.org/conversion/purchasing-power-parities-ppp.htm#indicator-chart
# To get comparable numbers, divide by this
PPP_EXCHANGE = {
    "Polska": 1.764,
    "Kalifornia, Stany Zjednoczone Ameryki": 1.,
    "Stan Waszyngton, Stany Zjednoczone Ameryki": 1.,
    "Stan Nowy Jork, Stany Zjednoczone Ameryki": 1.,
    "Inny stan, Stany Zjednoczone Ameryki": 1.,
    "USA": 1.,
    "Austria": 0.763,
    "Belgia": 0.758,
    "Czechy": 12.526,
    "Dania": 6.656,
    "Francja": 0.731,
    "Niemcy": 0.743,
    "Szwajcaria": 1.159,
    "Wielka Brytania": 0.684,
    "Hiszpania": 0.626,
    "Holandia": 0.786,
    "Irlandia": 0.807,
    "Szwecja": 8.877,
    "wietnam": None,
    "Azja (waluta USD)": None,  # not including PPP would be 1.
}

# CSV keys
COUNTRY = "Kraj/stan zamieszkania"
TOTAL_COMP = "Łączne roczne zarobki w narodowej walucie tego kraju"
BASE_COMP = "Podstawowa roczna pensja w narodowej walucie tego kraju"
GRADUATION_YEAR = "Rok ukończenia ostatniego kierunku na wydziale MIM"
EMPLOYMENT_KIND = "Sposób zatrudnienia"
WORK_HOURS = "Liczba faktycznych godzin pracy w typowym tygodniu"
DEGREE = "Kierunek związany ze stopniem w poprzednim pytaniu"
GENDER = "Płeć"
PROFESSION = "Główny zawód wykonywany w 2019"
HIGHEST_EDUCATION = "Najwyższy stopień naukowy ogółem (jeśli inny niż powyżej)"
HIGHEST_EDU_MISSPELLED = "Najwyższy stopień naukowy ogółem (jeśli inne niż powyżej)"
MIM_EDUCATION = "Najwyższy stopień naukowy uzyskany na wydziale MIM"
COMPANY_SIZE = "Liczba pracowników firmy/instytucji"
CITY_SIZE = "Liczba mieszkańców miejsca zamieszkania"
MIM_SATISFACTION = "W jakim stopniu studia na MIMie pomogły Ci w osiągnięciu obecnej kariery"


def data_cleanup(data):
  clean_data = []
  for response in data:
    if not response[TOTAL_COMP] and response[BASE_COMP]:
      response[TOTAL_COMP] = response[BASE_COMP]

    if HIGHEST_EDU_MISSPELLED in response:
      assert HIGHEST_EDUCATION not in response
      response[HIGHEST_EDUCATION] = response[HIGHEST_EDU_MISSPELLED]

    if response[MIM_EDUCATION] and not response[HIGHEST_EDUCATION]:
      response[HIGHEST_EDUCATION] = response[MIM_EDUCATION]

    if response[TOTAL_COMP]:
      response[TOTAL_COMP] = float(response[TOTAL_COMP])

    if response[BASE_COMP]:
      response[BASE_COMP] = float(response[BASE_COMP])

    if response[WORK_HOURS]:
      response[WORK_HOURS] = float(response[WORK_HOURS])

    if response[EMPLOYMENT_KIND] == "bezrobotny szukający pracy":
      response[TOTAL_COMP] = 0.

    if response[COUNTRY] == "Stan Washington, Stany Zjednoczone Ameryki":
      response[COUNTRY] = "Stan Waszyngton, Stany Zjednoczone Ameryki"

    if response[PROFESSION] == "Korepetytor":
      response[PROFESSION] = "nauczyciel / prowadzący szkolenia"

    if response[PROFESSION] == "devops/sysadmin/konfiguracja sieci - wszystko po trochu":
      response[PROFESSION] = "administrator sieci komputerowych"

    if response[PROFESSION] == "doktorant":
      response[PROFESSION] = "pracownik akademicki"

    clean_data.append(response)

  return clean_data


def read_data(filename="data_initial.csv"):
  reader = csv.DictReader(open(filename))
  data = list(reader)

  return data_cleanup(data)


def _ordered_counter(data, key):
  counter = collections.Counter([r[key] for r in data])
  ordered = collections.OrderedDict(counter.most_common())
  return ordered


def _process_small_groups(overall):
  last_group_id = 5
  other_values = [k for i, k in enumerate(overall.keys())
      if i > last_group_id or (
        last_group_id + 1 < len(overall) and overall[k] == list(overall.values())[last_group_id + 1])]
  num_other_values = sum([overall[k] for k in other_values])
  for value in other_values:
    overall.pop(value)

  if num_other_values:
    overall["inne"] = num_other_values
  return overall


def _process_label(label):
  if '/' in label:
    return label[:label.find('/')]
  
  return label


def _prepare_legend(axes):
  all_handles = []
  all_labels = []
  for ax in axes:
    handles, labels = ax.get_legend_handles_labels()
    for h, l in zip(handles, labels):
      if l not in all_labels:
        all_handles.append(h)
        all_labels.append(l)

  if "inne" in all_labels:
    idx = all_labels.index("inne")
    all_labels = all_labels[:idx] + all_labels[idx+1:] + [all_labels[idx]]
    all_handles = all_handles[:idx] + all_handles[idx+1:] + [all_handles[idx]]

  return all_handles, all_labels


def pie_per_degree(data, key, group_key):
  filtered_data = [dict(r) for r in data if r[key] and r[group_key]]
  for i, r in enumerate(filtered_data):
    if "Stany Zjednoczone Ameryki" in r[key]:
      r[key] = "USA"

  per_degree = collections.defaultdict(lambda: [])
  for r in filtered_data:
    per_degree[r[group_key]].append(r)
  
  degrees = [degree
      for degree, responses in per_degree.items() if len(responses) >= 5]

  groups_overall = _ordered_counter(filtered_data, key)
  print("here", groups_overall, degrees)

  all_colors = dict(zip(["inne"] + list(groups_overall.keys()),
    ["tab:grey", "tab:green", "tab:red", "tab:blue", "tab:orange", "tab:olive",
     "tab:purple", "tab:brown", "tab:cyan", "black", "yellow", "red", "green", "blue", "white", "pink", "purple"]))
  print("all_colors", all_colors)

  groups_overall = _process_small_groups(groups_overall)

  colors = [all_colors[c] for c in groups_overall.keys()]
  fig, axes = plt.subplots(2, (len(degrees) + 2)//2)
  axes = axes.flatten()
  labels = [_process_label(l) for l in groups_overall.keys()]
  # TODO: consider giving absolute numbers instead of percentage with
  def autopct_format(values):
    def my_format(pct):
        total = sum(values)
        val = int(round(pct*total/100.0))
        return '{v:d}'.format(v=val)
    return my_format

  axes[0].pie(groups_overall.values(), labels=labels, autopct='%1.0f%%', colors=colors)
  axes[0].set_title("ogółem")

  for did, d in enumerate(degrees):
    print(d)
    axes[did + 1].set_title(d)
    within_degree_values = _ordered_counter(per_degree[d], key)
    within_degree_values = _process_small_groups(within_degree_values)

    print("all_colors", all_colors)

    colors = [all_colors[c] for c in within_degree_values.keys()]
    print("colors", colors)

    labels = [_process_label(l) for l in within_degree_values.keys()]
    print("labels", labels)
    axes[did + 1].pie(within_degree_values.values(), labels=labels, autopct='%1.0f%%', colors=colors)

  handles, labels = _prepare_legend(axes)
  # fig.legend(handles, labels)

  fig.show()


def comp_distribution(data):
  incomes_filtered = _filter_incomes(data)
  filtered_data = [r for r in incomes_filtered if r[COUNTRY]]
  incomes_pln, incomes_ppp, median_pln, median_ppp = _process_incomes(filtered_data, TOTAL_COMP)
  print("median PLN", median_pln, "median PPP", median_ppp)

  fig, axes = plt.subplots(1, 2)
  fig.suptitle("Łączne średnie miesięczne zarobki")
  axes[0].set_title("nominalnie")
  axes[0].set_xlabel("tys. PLN")
  axes[0].set_ylabel("liczba absolwentów")
  h, _, _ = axes[0].hist(incomes_pln, bins=40, label="rozkład zarobków")
  axes[0].plot([median_pln, median_pln], [0, max(h)], linestyle="dashed", label=f"mediana={median_pln:.3f}", linewidth=2.)
  axes[0].legend()

  axes[1].set_title("po uwzględnieniu parytetu siły nabywczej (PPP)")
  axes[1].set_xlabel("tys. PLN")
  axes[1].set_ylabel("liczba absolwentów")
  h, _, _ = axes[1].hist(incomes_ppp, bins=40, label="rozkład zarobków")
  axes[1].plot([median_ppp, median_ppp], [0, max(h)], linestyle="dashed", label=f"mediana={median_ppp:.3f}", linewidth=2.)
  axes[1].legend()

  fig.show()


def base_vs_total_comp(data):
  filtered_data = _filter_incomes(data)
  ax = plt.subplot()

  _, total_incomes_ppp, _, total_median_ppp = _process_incomes(filtered_data, TOTAL_COMP)

  has_base = [r for r in filtered_data if r[BASE_COMP] != '']
  _, base_incomes_ppp, _, base_median_ppp = _process_incomes(has_base, BASE_COMP)

  print("Total comp median PPP", total_median_ppp, "base comp median PPP", base_median_ppp)

  max_income = int(max(total_incomes_ppp))
  bin_width = 10
  max_bin = max_income + bin_width - max_income % bin_width
  bins = list(range(0, max_bin + bin_width, bin_width))
  ticks = [b + bin_width//2 for b in bins]

  vals, _, _ = ax.hist([total_incomes_ppp, base_incomes_ppp], bins=bins, label=["łączne zarobki", "podstawowa pensja"], color=["tab:blue", "tab:orange"], alpha=0.7)
  ax.set_xlabel("tys. PLN, po uwzględnieniu PPP")
  ax.set_ylabel("liczba absolwentów")
  ax.set_xticks(bins)
  max_vals = int(vals.max())
  ax.set_yticks(range(0, max_vals + 3, 5))
  ax.set_title("Rozkład miesięcznych zarobków, uwzględniając bonusy lub nie")

  ax.plot([base_median_ppp, base_median_ppp], [0, max_vals], color="white", linewidth=4.5)
  ax.plot([base_median_ppp, base_median_ppp], [0, max_vals], linestyle="dashed", color="tab:orange", linewidth=2., label=f"mediana podstawowej pensji={base_median_ppp:.3f}")

  ax.plot([total_median_ppp, total_median_ppp], [0, max_vals], color="white", linewidth=4.5)
  ax.plot([total_median_ppp, total_median_ppp], [0, max_vals], linestyle="dashed", color="tab:blue", linewidth=2., label=f"mediana łącznych zarobków={total_median_ppp:.3f}")
  
  plt.legend()
  plt.show()


def working_hours_dist(data):
  filtered_data = [r for r in data if r[WORK_HOURS]]
  work_hours = [r[WORK_HOURS] for r in filtered_data]
  bins = [min(work_hours), 30, 35, 40, 45, 50, 55, 60, 65, 70, max(work_hours)+1]
  plt.title("Liczba godzin pracy w typowym tygodniu")
  plt.xlabel("liczba godzin")
  plt.ylabel("liczba absolwentów")
  plt.hist(work_hours, bins)
  plt.xticks(bins)
  plt.show()


def mim_satisfaction_dist(data):
  filtered_data = [r for r in data if r[MIM_SATISFACTION]]
  satisfaction = sorted([r[MIM_SATISFACTION] for r in filtered_data])
  plt.title("Wpływ studiów na MIMie na karierę")
  plt.xlabel("stopień")
  plt.ylabel("liczba absolwentów")
  _, bins, _ = plt.hist(satisfaction, bins=6, edgecolor="white")
  plt.xticks([b + 0.5 for b in bins])

  plt.show()


def _filter_incomes(data):
  clean_data = []
  empty = 0
  below_minimum = 0
  for response in data:
    if response[TOTAL_COMP] == '':
      empty += 1
      continue

    if response[EMPLOYMENT_KIND] == "bezrobotny nieszukający pracy":
      continue

    if response[WORK_HOURS]:
      weekly_equivalent = response[TOTAL_COMP] / 52. * 40. / response[WORK_HOURS]
    else:
      weekly_equivalent = response[TOTAL_COMP] / 52.

    if response[EMPLOYMENT_KIND] != "bezrobotny szukający pracy":
      if response[COUNTRY] == "Polska" and weekly_equivalent < 14.70 * 40:
        # below minimal salary, likely given monthly one or /1000.
        below_minimum += 1
        continue

      if response[COUNTRY] == "Wielka Brytania" and weekly_equivalent < 7.83 * 40:
        # below minimal salary, likely given monthly one or /1000.
        below_minimum += 1
        continue

    if not response[COUNTRY] or PPP_EXCHANGE[response[COUNTRY]] is None:
      empty += 1
      # Don't have the data to compare PPP.
      continue

    clean_data.append(response)

  print(len(clean_data), "datapoints with income, out of", len(data), len(clean_data)/len(data), "empty", empty, "below minimum", below_minimum)
  return clean_data


def _process_incomes(data, key):
  incomes_pln = sorted([
    r[key] / 1000. / 12. * CURRENCY_EXCHANGE[r[COUNTRY]] for r in data])
  incomes_ppp = sorted([
    r[key] / 1000. /12. / PPP_EXCHANGE[r[COUNTRY]] * PPP_EXCHANGE["Polska"]
    for r in data if PPP_EXCHANGE[r[COUNTRY]] is not None])

  def _median(l):
    if len(l) % 2 == 1:
      return l[len(l)//2]
    return (l[len(l)//2 - 1] + l[len(l)//2])/2.

  median_pln = _median(incomes_pln)
  median_ppp = _median(incomes_ppp)

  return incomes_pln, incomes_ppp, median_pln, median_ppp


def median_comp_in_group(data, group):
  incomes_filtered = _filter_incomes(data)
  filtered_data = [dict(r) for r in incomes_filtered if r[group]]
  if group == COUNTRY:
    for i, r in enumerate(filtered_data):
      if "Stany Zjednoczone Ameryki" in r[COUNTRY]:
        r[COUNTRY] = "USA"

  per_group = collections.defaultdict(lambda: [])
  for r in filtered_data:
    per_group[r[group]].append(r)

  if group == HIGHEST_EDUCATION:
    def key(x):
      if x == "licencjat": return 0
      if x == "magister": return 1
      if x == "doktor": return 2
  else:
    key = None

  group_values = sorted([
      group for group, responses in per_group.items() if len(responses) >= 5],
      key=key)

  if group == COUNTRY:
    both = True
  else:
    both = False

  fig, axes = plt.subplots(1, 2 if both else 1)
  if group == HIGHEST_EDUCATION:
    title_group = "Najwyższy stopień naukowy ogółem"
  elif group == DEGREE:
    title_group = "Kierunek"
  else:
    title_group = group

  fig.suptitle(f"{title_group} a mediana łącznych miesięcznych zarobków")
  for i, ax in enumerate(axes):
    if i == 0:
      ax.set_ylabel("tys. PLN, biorąc pod uwagę PPP")
    else:
      ax.set_ylabel("tys. PLN (nominalnie)")

    ax.set_xlabel(title_group)

    group_medians = []
    deviations = []
    canonical_values = []
    num_samples = []

    for g in group_values:
      if '/' in g:
        canonical_values.append(g[:g.find('/')])
      else:
        canonical_values.append(g)

      subdata = [r for r in filtered_data if r[group] == g]
      incomes_pln, incomes_ppp, group_median_pln, group_median_ppp = _process_incomes(subdata, TOTAL_COMP)
      if i == 0:
        incomes = incomes_ppp
        group_median = group_median_ppp
      else:
        incomes = incomes_pln
        group_median = group_median_pln

      group_medians.append(group_median)
      k = 10
      lower_perc = group_median - np.percentile(incomes, 50-k)
      higher_perc = np.percentile(incomes, 50+k) - group_median
      deviations.append([lower_perc, higher_perc])
      num_samples.append(len(incomes))

    bars = ax.bar(list(range(len(group_medians))), group_medians, yerr=list(zip(*deviations)))

    ax.set_xticks(list(range(len(group_medians))))
    ax.set_xticklabels(canonical_values)
    for idx, rect in enumerate(bars):
      height = rect.get_height()
      ax.text(rect.get_x() + rect.get_width()/2., 1., num_samples[idx],
               ha='center', va='bottom')

  fig.show()


def abroad_graduation_year(data):
  filtered_data = [r for r in data if r[COUNTRY] and r[GRADUATION_YEAR]]
  graduation_years = sorted(list(set([r[GRADUATION_YEAR] for r in filtered_data])))

  perc_abroad = []
  for g in graduation_years:
    subdata = [0. if r[COUNTRY] == "Polska" else 1. for r in filtered_data if r[GRADUATION_YEAR] == g]
    perc_abroad.append(np.mean(subdata))

  plt.bar(list(range(len(graduation_years))), perc_abroad)
  plt.xticks(list(range(len(graduation_years))), graduation_years)

  plt.show()


def filling_time(data):
  timestamps_str = [r["Timestamp"] for r in data if r["Timestamp"]]
  timestamps = [datetime.strptime(t, "%d/%m/%Y %H:%M:%S") for t in timestamps_str]

  fig, ax = plt.subplots(1,1)
  _, bins, _ = ax.hist(timestamps, bins=30, )
  ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:00"))
  ax.set_ylabel("liczba absolwentów")
  ax.set_xlabel("czas")
  ax.set_title("Rozkład czasu wypełenienia ankiety")
  fig.show()


def to_run(data):
  pie_per_degree(data, COUNTRY, DEGREE)
  pie_per_degree(data, GENDER, DEGREE)
  pie_per_degree(data, PROFESSION, DEGREE)
  pie_per_degree(data, COUNTRY, HIGHEST_EDUCATION)
  pie_per_degree(data, PROFESSION, HIGHEST_EDUCATION)
  pie_per_degree(data, PROFESSION, EMPLOYMENT_KIND)
  comp_distribution(data)
  base_vs_total_comp(data)
  working_hours_dist(data)
  mim_satisfaction_dist(data)

  median_comp_in_group(data, GENDER)
  median_comp_in_group(data, COUNTRY)
  median_comp_in_group(data, DEGREE)  # bioinf error bars look wrong, but it's ok.
  median_comp_in_group(data, GRADUATION_YEAR)
  median_comp_in_group(data, HIGHEST_EDUCATION)
  median_comp_in_group(data, PROFESSION)
  median_comp_in_group(data, MIM_SATISFACTION)

  filling_time(data)
