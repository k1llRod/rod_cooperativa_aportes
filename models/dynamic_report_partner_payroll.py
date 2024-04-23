from odoo import api, models, fields
from odoo.tools.misc import xlsxwriter
from odoo.exceptions import UserError
import xlsxwriter

class DynamicReportPartnerPayroll(models.Model):
    _name = 'dynamic.report.partner.payroll'
    _description = 'Dynamic Report: Partner Payroll'

    date_from = fields.Date(string="Desde")
    date_to = fields.Date(string="Hasta")
    report_type = fields.Selection([('active_service','Servicio activo'),
                                    ('passive_reserve_a','Categoria A'),
                                    ('passive_reserve_b','Categoria B')], string="Tipo de reporte")

    @api.model
    def purchase_report(self, option):
        orders = self.env['partner.payroll'].search([])
        report_values = self.env['dynamic.report.partner.payroll'].search(
            [('id', '=', option[0])])
        data = {

            'report_type': report_values.report_type,
            'model': self,
        }
        if report_values.date_from:
            data.update({
                'date_from': report_values.date_from,
            })
        if report_values.date_to:
            data.update({
                'date_to': report_values.date_to,
            })
        filters = self.get_filter(option)
        # report = self._get_report_values(data)
        # lines = self._get_report_values(data).get('PURCHASE')
        lines = self._get_report_values(data)
        return {
            'name': "Purchase Orders",
            'type': 'ir.actions.client',
            'tag': 'a_r',
            'orders': data,
            'filters': filters,
            'report_lines': lines,
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}
        if data.get('report_type') == 'report_by_order':
            filters['report_type'] = 'Report By Order'
        return filters

    def get_filter_data(self, option):
        r = self.env['dynamic.report.partner.payroll'].search([('id', '=', option[0])])
        default_filters = {}
        filter_dict = {
            'report_type': r.report_type,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_report_sub_lines(self, data, report, date_from, date_to):
        report_sub_lines = []
        new_filter = None
        if data.get('report_type') == 'report_by_order':
            query = '''
                    select * from partner_payroll
                             '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by l.user_id,res_users.partner_id,res_partner.name,l.partner_id,l.date_order,l.name,l.amount_total,l.notes,l.id"
            self._cr.execute(query)
            report_by_order = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order)
        elif data.get('report_type') == 'report_by_product':
            query = '''
                    select * from partner_payroll
                              '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            # query += "group by l.amount_total,purchase_order_line.name,purchase_order_line.price_unit,purchase_order_line.product_id,product_product.default_code,product_template.categ_id,product_category.name"
            self._cr.execute(query)
            report_by_product = self._cr.dictfetchall()
            report_sub_lines.append(report_by_product)
        return report_sub_lines

    def _get_report_values(self, data):
        docs = data['model']
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        if data['report_type'] == 'active_service':
            report = ['Reporte Socios Servicio Activo']
        elif data['report_type'] == 'passive_reserve_a':
            report = ['Reporte Socios Categoria A']
        elif data['report_type'] == 'passive_reserve_b':
            report = ['Reporte Socios Categoria B']
        else:
            report = ['Reporte Socios']

        if data.get('report_type'):
            report_res = \
                self._get_report_sub_lines(data, report, date_from, date_to)[0]
        else:
            report_res = self._get_report_sub_lines(data, report, date_from,
                                            date_to)
        return {
            'doc_ids': self.ids,
            'docs': docs,
            'PARTNER_PAYROLL': report_res,
        }
