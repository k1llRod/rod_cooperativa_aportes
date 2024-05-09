from odoo import models, fields, api
import io
import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DynamicReportPartnerPayroll(models.Model):
    _name = "dynamic.report.partner.payroll"
    purchase_report = fields.Char(string="Purchase Report")
    date_from = fields.Datetime(string="Date From")
    date_to = fields.Datetime(string="Date to")
    report_type = fields.Selection([
        ('report_by_order', 'Report By Order'),
        ('report_by_product', 'Report By Product')], default='report_by_order')

class DynamicPurchaseReport(models.Model):
    _name = "dynamic.purchase.report"
    purchase_report = fields.Char(string="Purchase Report")
    date_from = fields.Datetime(string="Date From")
    date_to = fields.Datetime(string="Date to")
    report_type = fields.Selection([
        ('report_by_order', 'Report By Order'),
        ('report_by_product', 'Report By Product')], default='report_by_order')


