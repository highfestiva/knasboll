#!/usr/bin/env python3

import argparse
from datetime import datetime
import dateutil.parser
import csv
import xml.etree.ElementTree as ET


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', default='generic_xml.xml', help='invoice XML file to process')
    parser.add_argument('-o', '--output-file', default='dalas-invoice-import.csv', help='output CSV file for import into book-keeping software')
    options = parser.parse_args()

    table = []
    ns = dict([node for _, node in ET.iterparse(options.input_file, events=['start-ns'])])
    ns['ns'] = ns['']
    e = ET.parse(options.input_file).getroot()
    for account in e.findall('ns:account', ns):
        customer = account.find('ns:cust_name', ns).text
        for invoice in account.findall('ns:invoice', ns):
            date = invoice.find('ns:invoice_date', ns).text
            timestamp = dateutil.parser.parse(date).timestamp()
            date = datetime.fromtimestamp(timestamp).isoformat().partition('T')[0]
            for invoice_item in invoice.findall('ns:invoice_item', ns):
                what = invoice_item.find('ns:allocation_code_name', ns).text
                price = invoice_item.find('ns:gross_amount', ns).text
                table += [(customer, date, what, price)]

    wf = open(options.output_file, 'w')
    wr = csv.writer(wf)
    wr.writerow(['Customer', 'Date', 'Item', 'Price'])
    for row in table:
        wr.writerow(row)
    wf.close()
    total = sum(float(r[-1]) for r in table)
    print('Dala, your bester agent havs convertidid the %i invoice thingies for totals %.2f evro and writing it to %s!' % (len(table), total, options.output_file))


if __name__ == '__main__':
    main()
