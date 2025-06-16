from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo.http import request


class WizardReportForm(models.TransientModel):
    _name = 'wizard.report.form'
    partner_status_especific = fields.Selection(
        [('active_service', 'Servicio activo'), ('letter_a', 'Letra "A" de disponibilidad'),
         ('passive_reserve_a', 'Reserva pasivo "A"'),
         ('passive_reserve_b', 'Reserva pasivo "B"'),
         ('leave', 'Baja')], string='Tipo de asociado', store=True)

    partner_status_especific_status = fields.Selection(
        [('active_service', 'Servicio activo'), ('letter_a', 'Letra "A" de disponibilidad'),
         ('passive_reserve_a', 'Reserva pasivo "A"'),
         ('passive_reserve_b', 'Reserva pasivo "B"'),
         ('leave', 'Baja')], string='Tipo de asociado', store=True)

    def report_loan(self):
        print('EXCEL print', self.read()[0])
        partner_payroll = self.env['partner.payroll'].search([('partner_status_especific','=',self.partner_status_especific)])
        data = {
            'loan': True,
            'partner_status_especific': self.partner_status_especific,
        }
        return self.env.ref('rod_cooperativa_aportes.report_report_form_loan_xlsx').report_action(self, data=data)

    def report_loan_category_b(self):
        # print('EXCEL print', self.read()[0])
        partner_payroll = self.env['partner.payroll'].search([('partner_status_especific','=',self.partner_status_especific)])
        data = {
            'loan': True,
            'partner_status_especific': self.partner_status_especific,
        }
        return self.env.ref('rod_cooperativa_aportes.report_report_category_b_xlsx').report_action(self, data=data)

    def report_state_partner(self):
        print('EXCEL print', self.read()[0])
        partner_payroll = self.env['partner.payroll'].search([('partner_status_especific', '=', '')])
        data = {
            'partner_payroll': partner_payroll,
        }
        return self.env.ref('rod_cooperativa_aportes.report_report_form_loan_xlsx').report_action(self, data=data)

    @api.model
    def print_xlsx_front(self, wizard_id):
        wizard = self.browse(wizard_id)
        print('EXCEL print', wizard.read()[0])

        data = {
            'loan': True,
            'partner_status_especific': wizard.partner_status_especific,
        }

        # Ejecuta el reporte definido con report_action
        action = request.env.ref('rod_cooperativa_aportes.report_report_category_b_xlsx').report_action(wizard,
                                                                                                        data=data)

        # Genera la URL de descarga
        return '/report/download?data=%s' % request.env['ir.actions.report']._encode_report_data(action)

    def report_xlsx(self):
        return self.env.ref('rod_cooperativa_aportes.report_report_category_b_xlsx').report_action(self)