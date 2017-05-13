import requests
from HTMLParser import HTMLParser

TOTALS_FILE = 'Totals.htm'
CPT_FILE = 'CPT.htm'
ICD10_FILE = 'ICD10.htm'

class TyphonTableParser(HTMLParser):
  def __init__(self):
    HTMLParser.__init__(self)
    self.append = False
    self.current_table = []
    self.current_table_number = 0
    self.current_table_title = None
    self.u = False
    self.b = False
    self.current_td = ''
    self.data = {}

  def handle_starttag(self, tag, attrs):
    if tag == 'table':
      self.append = True
      self.current_table = []
    elif tag == 'tr':
      self.current_table.append([])
    elif tag == 'u':
      self.u = True
    elif tag == 'b':
      self.b = True

  def handle_endtag(self, tag):
    if tag == 'table':
      if self.current_table_title is not None:
        self.data[self.current_table_title] = self.current_table
        self.current_table_title = None
      else:
        self.data['table%d' % self.current_table_number] = self.current_table
        self.current_table_number += 1
      self.current_table = []
      self.append = False
    elif tag == 'td':
      if self.current_table:
        self.current_table[-1].append(self.current_td)
      self.current_td = ''
    elif tag == 'u':
      self.u = False
    elif tag == 'b':
      self.b = False

  def handle_data(self, data):
    if self.append:
      self.current_td += data.strip()
    if self.b and self.u and self.current_table_title is None:
      self.current_table_title = data.strip()

def retrieve_data(input):
  with open(input, 'r') as f:
    parser = TyphonTableParser()
    parser.feed(f.read())
  res = dict(parser.data)
  return res

def organize_totals(data):
  res = {}
  res['age'] = data['AGE']

  clinical_experiences = dict((k.replace(':', ''), int(v)) for k, v in data['CLINICAL EXPERIENCES'][1:])
  res['clinical_experiences'] = clinical_experiences
  
  reason_for_visit  = dict((k.replace(':', ''), int(v)) for k, v in data['REASON FOR VISIT'][1:])
  res['reason_for_visit'] = reason_for_visit

  typehp = dict((k.replace(':', ''), int(v)) for k, v in data['TYPE OF H'][1:])
  res['type_h_p'] = typehp

  proc_skills = {}
  for row in data['PROCEDURES/SKILLS']:
    try:
      observed, assisted, performed = int(row[0]), int(row[1]), int(row[2])
      description = row[4]
      proc_skills[description] = dict(observed=observed, assisted=assisted, performed=performed)
    except:
      continue
  res['proc_skills'] = proc_skills

  return res

def organize_cpt(data):
  res = {}
  for name, table in data.iteritems():
    if table[0][0] == 'ALL CPT CODES':
      res['cpt_codes'] = dict((r[1].split(' - ', 1)[0], int(r[0])) for r in filter(lambda r: r[0] not in ('ALL CPT CODES', 'TOTAL', ''), table))
  return res

def organize_icd(data):
  res = {}
  for name, table in data.iteritems():
    if table[0][0] == 'ALL ICD CATEGORIES':
      res['icd_codes'] = dict((r[1].split('- ', 1)[0], int(r[0])) for r in filter(lambda r: r[0] not in ('ALL ICD CATEGORIES', 'TOTAL', ''), table))
  return res

def verify_data(label, args, match=True):
  verified = True
  values = args.values()
  if match:
    for i in range(len(values) - 1):
      if values[i] != values[i - 1]:
        verified = False
  else:
    for i in range(len(values) - 1):
      if values[i] == values[i - 1]:
        verified = False
  if verified:
    print '  %s verified (%s)' % (label, args.items())
  else:
    print '  [USER ACTION REQUIRED] Verifying %s failed: %s' % (label, args.items())

def verify(data):
  # A. Your Case Log totals report corresponds with the correct set of dates
  print '[USER ACTION REQUIRED] Make sure your Case Log totals report corresponds with the correct set of dates.'

  # B. The number of "Clinical Experiences (based on rotation type) =
  # "Geriatric" matches the number of patients seen that are >= 65?
  print 'Verifying: Geriatric patients...'
  geriatric_clinical_experiences = data['clinical_experiences']['Geriatrics']
  geriatric_breakdown_index = next(i for i, el in enumerate(data['age']) if el[0] == 'Geriatric Breakdown')
  geriatric_patients = sum(map(lambda x: int(x[1] or 0), data['age'][geriatric_breakdown_index + 1:]))
  verify_data('Geriatric patients', {'Geriatric patients': geriatric_patients, 'Geriatric Clinical Experiences': geriatric_clinical_experiences})

    # C. All encounters with Psychiatric disorders are marked as Rotation =
  # Psychiatric or Geri/Psych as appropriate.
  print '[USER ACTION REQUIRED] Make sure that all encounters with Psychiatric disorders are marked as Rotation = Psychiatric or Geri/Psych as appropriate.'

  # D. All ICD-10 and CPT codes are valid
  print '[USER ACTION REQUIRED] Make sure all ICD-10 and CPT codes are valid'

  # E. The numbers for: "Reason for visit", "Type of H&P" and "E&M CPT codes" match
  # For Example: Reason for visit = Annual/Well Person Exam;
  # Type of H&P = Comprehensive; CPT Code = 99382
  print 'Verifying: Reason for visit, Type of H&P, CPT codes match...'
  annual_visits = data['reason_for_visit'].get('Annual/Well-Person Exam', 0)
  comprehensive_hp = data['type_h_p'].get('Comprehensive', 0)
  annual_visits_cpt = sum(value for code, value in data['cpt_codes'].iteritems() if code.startswith('9939') or code.startswith('9938'))
  verify_data('Annual Visits', {'Reason for visit = Annual/Well-Person Exam': annual_visits, 'Type of H&P = Comprehensive': comprehensive_hp, 'CPT codes 9939X and 9938X': annual_visits_cpt})
  unmarked_reason_for_visit = data['reason_for_visit'].get('Unmarked', -1)
  unmarked_hp = data['type_h_p'].get('Unmarked', -1)
  verify_data('Unmarked Logs', {'Unmarked Reason for visit': unmarked_reason_for_visit, 'Unmarked Type of H&P': unmarked_hp, 'Required': 0})
  prob_focus_hp = data['type_h_p'].get('Problem Focused', 0)
  prob_focus_cpt = sum(value for code, value in data['cpt_codes'].iteritems() if code in ('99202', '99212'))
  verify_data('Problem Focused', {'Type of H&P = Problem Focused': prob_focus_hp, 'CPT codes 99202, 99212': prob_focus_cpt})
  exp_prob_focus_hp = data['type_h_p'].get('Expanded Prob. Focused', 0)
  exp_prob_focus_cpt = sum(value for code, value in data['cpt_codes'].iteritems() if code in ('99203', '99213', '99243'))
  verify_data('Expanded Problem Focused', {'Type of H&P = Expanded Problem Focus': exp_prob_focus_hp, 'CPT codes 99203, 99213, 99243': exp_prob_focus_cpt})
  detailed_hp = data['type_h_p'].get('Detailed', 0)
  detailed_cpt = sum(value for code, value in data['cpt_codes'].iteritems() if code in ('99204', '99214', '99244'))
  verify_data('Detailed', {'Type of H&P = Detailed': detailed_hp, 'CPT codes 99204, 99214, 99244': detailed_cpt})
  comprehensive_cpt = sum(value for code, value in data['cpt_codes'].iteritems() if code in ('99205', '99215'))
  verify_data('Comprehensive', {'Required': 0, 'CPT codes 99205, 99215': comprehensive_cpt})
  initial_visits = data['reason_for_visit'].get('Initial Visit', 0)
  initial_visits_cpt = sum(value for code, value in data['cpt_codes'].iteritems() if code.startswith('9920'))
  verify_data('Initial Visits', {'Reason for visit = Initial Visit': initial_visits, 'CPT codes 9920X': initial_visits_cpt})
  new_consults = data['reason_for_visit'].get('New Consult', 0)
  new_consults_cpt = sum(value for code, value in data['cpt_codes'].iteritems() if code.startswith('9924'))
  verify_data('New Consults', {'Reason for visit = New Consult': new_consults, 'CPT codes 9924X': new_consults_cpt})
  
  # F. The number of preventative health CPT codes (993-- ) match the
  # number of preventative health ICD-10 codes (Z00.0_ or Z00.1_)
  print 'Verifying: preventative health CPT (993XX) and ICD-10 (Z00) codes match...'
  phealth_cpt_codes = sum(value for code, value in data['cpt_codes'].iteritems() if code.startswith('993'))
  phealth_icd_codes = sum(value for code, value in data['icd_codes'].iteritems() if code.startswith('Z00'))
  verify_data('CPT vs ICD10', {'CPT codes 993XX': phealth_cpt_codes, 'ICD10 = Z00': phealth_icd_codes})

  # G. The report is complete (all pages have been included)
  print '[USER ACTION REQUIRED] Make sure the report is complete (all pages have been included)'


if __name__ == '__main__':
  all_data = {}
  all_data.update(organize_totals(retrieve_data(TOTALS_FILE)))
  all_data.update(organize_cpt(retrieve_data(CPT_FILE)))
  all_data.update(organize_icd(retrieve_data(ICD10_FILE)))

  verify(all_data)

