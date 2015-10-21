#!/usr/bin/python
# -*- coding: utf-8 -*-

# generate_uid_2015b.py

"""
    Reformat the UID list (Table A-1 PS3.6-2015b) from the PS3.6 docbook file to Python syntax
    
    Write the dict element as:
    UID: (name, type, info, is_retired)
    
    info is extra information extracted from very long names, e.g.
        which bit size a particular transfer syntax is default for
    is_retired is 'Retired' if true, else ''
"""

# Based on Rickard Holmberg's docbook_to_uiddict2013.py
# http://code.google.com/r/rickardholmberg-pydicom/
# but rewritten so not using bs4

import urllib2
import xml.etree.ElementTree as ET
import os

pydict_filename = '../dicom/_UID_dict.py'
dict_name = 'UID_dictionary'

def write_dict(f, dict_name, attributes):
    entry_format = """'{UID Value}': ('{UID Name}', '{UID Type}', '{UID Info}', '{Retired}')"""
        
    f.write("\n%s = {\n    " % dict_name)
    f.write(",\n    ".join(entry_format.format(**attr) for attr in attributes))
    f.write("\n}\n")

def parse_docbook_table(book_root, caption, empty_field_name="Retired"):
    """ Parses the given XML book_root for the table with caption matching caption for DICOM Element data 
    
    Returns a list of dicts with each dict representing the data for an Element from the table
    """
    
    br = '{http://docbook.org/ns/docbook}' # Shorthand variable
    
    # Find the table in book_root with caption
    for table in book_root.iter('%stable' %br):
        if table.find('%scaption' %br).text == caption:
            
            def parse_row(column_names, row):
                """ Parses the table's tbody tr row, row, for the DICOM Element data 
                
                Returns a list of dicts {header1 : val1, header2 : val2, ...} with each list an Element
                """
                
                cell_values = []
                
                # The row should be <tbody><tr>...</tr></tbody>
                # Which leaves the following:
                #   <td><para>Value 1</para></td>
                #   <td><para>Value 2</para></td>
                #   etc...
                # Some rows are 
                #   <td><para><emphasis>Value 1</emphasis></para></td>
                #   <td><para><emphasis>Value 2</emphasis></para></td>
                #   etc...
                # There are also some without text values
                #   <td><para/></td>
                #   <td><para><emphasis/></para></td>
                
                for cell in row.iter('%spara' %br):
                    # If we have an emphasis tag under the para tag
                    emph_value = cell.find('%semphasis' %br)
                    if emph_value is not None:
                        # If there is a text value add it, otherwise add ""
                        if emph_value.text is not None:
                            cell_values.append(emph_value.text.strip().replace(u"\u200b", "")) #200b is a zero width space
                        else:
                            cell_values.append("")
                    # Otherwise just grab the para tag text
                    else:
                        if cell.text is not None:
                            cell_values.append(cell.text.strip().replace(u"\u200b", ""))
                        else:
                            cell_values.append("")
                
                cell_values[3] = ''
                cell_values.append('')
                
                if '(Retired)' in cell_values[1]:
                    cell_values[4] = 'Retired'
                    cell_values[1] = cell_values[1].replace('(Retired)', '').strip()
                
                if ':' in cell_values[1]:
                    cell_values[3] = cell_values[1].split(':')[-1].strip()
                    cell_values[1] = cell_values[1].split(':')[0].strip()
                
                return {key : value for key, value in zip(column_names, cell_values)}
            
            # Get all the Element data from the table
            column_names = ['UID Value', 'UID Name', 'UID Type', 'UID Info', 'Retired']
            attrs = [parse_row(column_names, row) for row in table.find('%stbody' %br).iter('%str' %br)]

            return attrs

attrs = []

url = 'http://medical.nema.org/medical/dicom/current/source/docbook/part06/part06.xml'
response = urllib2.urlopen(url)
tree = ET.parse(response)
root = tree.getroot()

attrs += parse_docbook_table(root, "UID Values")

for attr in attrs:
    attr['UID Name'] = attr['UID Name'].replace('&', 'and')
    attr['UID Value'] = attr['UID Value'].replace(u'\u00ad', '')

py_file = file(pydict_filename, "wb")
py_file.write("# %s\n" % os.path.basename(pydict_filename))
py_file.write('"""\nDictionary of UID: (name, type, name_info, is_retired)\n\n"""')
py_file.write('\n# Auto-generated by %s\n' % os.path.basename(__file__))
write_dict(py_file, dict_name, attrs)

py_file.close()

print ("Finished creating python file %s containing the UID dictionary" % pydict_filename)
print ("Wrote %d UIDs" % len(attrs))
