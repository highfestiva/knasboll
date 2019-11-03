#!/usr/bin/env python3

import argparse
import csv
from datetime import datetime
import dateutil.parser
from glob import glob
import xml.etree.ElementTree as ET


columns = [ 'allocation', 'invoice_no', 'invoice_date', 'pay_date', 'customer_number',
            'tax_total', 'tax_total_s', 'invoice_total', 'invoice_total_s', 'allocation_code',
          ]


def add_col(table, inp_col, new_col, func):
    global columns
    columns += [new_col]
    for row in table:
        i = columns.index(inp_col)
        val = row[i]
        row += [func(val)]


def main():
    print('knasboll v0.4')
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-wildcard', default='*.xml', help='invoice XML files to process')
    parser.add_argument('-o', '--output-file', default='dalas-invoice-import.csv', help='output Excel file for import into book-keeping software')
    options = parser.parse_args()

    # load table
    allocation_lookup = eval(open('allocation.cfg').read())

    table = []
    for fn in glob(options.input_wildcard):
        print('processing %s...' % fn)
        # load import file and place each row in table
        ns = dict([node for _,node in ET.iterparse(fn, events=['start-ns'])])
        ns['ns'] = ns['']
        e = ET.parse(fn).getroot()
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
                allocs = []
                for invoice_item in invoice.findall('ns:invoice_item', ns):
                    allocation = invoice_item.find('ns:allocation_code_name', ns).text
                    if allocation not in allocation_lookup:
                        print('FATAL: no such allocation %s in allocation.cfg' % allocation)
                        return
                    allocation_code = allocation_lookup[allocation]
                    allocs += [(allocation_code,allocation)]
                allocation_code, allocation = sorted(allocs)[0]
                table += [[allocation, invoice_number, invoice_date, payment_date, customer_id, tax_total, tax_total_s, invoice_total, invoice_total_s, allocation_code]]

    add_col(table, 'invoice_date', 'year', lambda s: s.split('-')[0])
    add_col(table, 'invoice_date', 'month', lambda s: s.split('-')[1])
    add_col(table, 'invoice_date', 'journal', lambda x: '70')
    add_col(table, 'invoice_date', 'payment_condition', lambda x: '01')
    add_col(table, 'invoice_date', 'vat_code', lambda x: '04')
    add_col(table, 'invoice_date', 'currency', lambda x: 'EUR')
    add_col(table, 'invoice_date', 'exchange_fact', lambda x: 1.0)
    cols = ['journal','year','month','invoice_no','allocation','invoice_date','pay_date','currency','exchange_fact','payment_condition','customer_number','allocation_code','allocation','vat_code','invoice_total','tax_total']

    wf = open(options.output_file, 'w', newline='')
    wr = csv.writer(wf)
    t = [[row[columns.index(c)] for row in table] for c in cols]
    for row in zip(*t):
        wr.writerow(row)
    wf.close()

    # finish with a nice message
    gross_total = sum(row[columns.index('invoice_total')] for row in table)
    net_total = gross_total - sum(row[columns.index('tax_total')] for row in table)
    print('Dala, your bester agent havs convertidid the %i invoice thingies for gross %.2f evro/net %.2f evrossar and writing it to %s!' % (len(table), gross_total, net_total, options.output_file))


if __name__ == '__main__':
    main()
    input('Pressers enter!!!')
