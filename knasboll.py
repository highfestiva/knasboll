#!/usr/bin/env python3

import argparse
import csv
from datetime import datetime
import dateutil.parser
import pandas as pd
import xml.etree.ElementTree as ET


columns = [ 'allocation', 'invoice_no', 'invoice_date', 'pay_date', 'customer_number',
            'tax_total', 'tax_total_s', 'invoice_total', 'invoice_total_s', 'allocation_code',
          ]


def main():
    print('knasboll v0.4')
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file', default='generic_xml.xml', help='invoice XML file to process')
    parser.add_argument('-o', '--output-file', default='dalas-invoice-import.csv', help='output Excel file for import into book-keeping software')
    options = parser.parse_args()

    # load table
    allocation_lookup = eval(open('allocation.cfg').read())

    # load import file and place each row in table
    table = []
    ns = dict([node for _,node in ET.iterparse(options.input_file, events=['start-ns'])])
    ns['ns'] = ns['']
    e = ET.parse(options.input_file).getroot()
    for account in e.findall('ns:account', ns):
        customer_id = account.find('ns:cust_id', ns).text
        for invoice in account.findall('ns:invoice', ns):
            invoice_date = invoice.find('ns:invoice_date', ns).text
            timestamp = dateutil.parser.parse(invoice_date).timestamp()
            invoice_date = datetime.fromtimestamp(timestamp).isoformat().partition('T')[0]
            payment_date = invoice.find('ns:payment_due_date', ns).text
            timestamp = dateutil.parser.parse(payment_date).timestamp()
            payment_date = datetime.fromtimestamp(timestamp).isoformat().partition('T')[0]
            tax_total = invoice.find('ns:total_tax_value', ns).text
            tax_total = float(tax_total)
            tax_total_s = ('%.2f'%float(tax_total)).replace('.',',')
            invoice_total = invoice.find('ns:invoice_total', ns).text
            invoice_total = float(invoice_total) + tax_total
            invoice_total_s = ('%.2f'%invoice_total).replace('.',',')
            invoice_number = invoice.find('ns:invoice_number', ns).text
            for invoice_item in invoice.findall('ns:invoice_item', ns):
                allocation = invoice_item.find('ns:allocation_code_name', ns).text
                break
            if allocation not in allocation_lookup:
                print('FATAL: no such allocation %s in allocation.cfg' % allocation)
                return
            allocation_code = allocation_lookup[allocation]
            table += [(allocation, invoice_number, invoice_date, payment_date, customer_id, tax_total, tax_total_s, invoice_total, invoice_total_s, allocation_code)]

    df = pd.DataFrame(table, columns=columns)
    df['year'] = pd.DatetimeIndex(df['invoice_date']).year
    df['month'] = pd.DatetimeIndex(df['invoice_date']).month
    df['journal'] = '70'
    df['payment_condition'] = '01'
    df['vat_code'] = '04'
    df['currency'] = 'EUR'
    df['exchange_fact'] = 1.0
    cols = ['journal','year','month','invoice_no','allocation','invoice_date','pay_date','currency','exchange_fact','payment_condition','customer_number','allocation_code','allocation','vat_code','invoice_total','tax_total']
    # df1.to_excel(options.output_file, index=False, header=False)
    wf = open(options.output_file, 'w', newline='')
    wr = csv.writer(wf)
    for row in zip(*[df[c] for c in cols]):
        print(row)
        wr.writerow(row)
    wf.close()

    # finish with a nice message
    total = df['invoice_total'].sum()
    print('Dala, your bester agent havs convertidid the %i invoice thingies for totals %.2f evro and writing it to %s!' % (len(table), total, options.output_file))


if __name__ == '__main__':
    main()
