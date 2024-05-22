from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class ReportForm(models.Model):
    _name = 'report.form'

    partner_status_especific = fields.Selection([('active_service', 'Servicio activo'),('letter_a', 'Letra "A" de disponibilidad'),
                                                 ('passive_reserve_a', 'Reserva pasivo "A"'),
                                                 ('passive_reserve_b', 'Reserva pasivo "B"'),
                                                 ('leave', 'Baja')], string='Tipo de asociado', store=True)

    def report_loan(self):
        print('EXCEL print', self.read()[0])

        data = {
            'form_data': self.read()[0],
        }
        return self.env.ref('rod_cooperativa_aportes.report_report_form_loan_xlsx').report_action(self, data=data)



        # return {
        #     'type': 'ir.actions.report',
        #     'report_name': 'rod_cooperativa_aportes.report_loan',
        #     'data': {
        #         'model' : 'report.form',
        #         'options': json.dumps(data, default=date_utils.json_default()),
        #         'output_format': 'xlsx',
        #         'report_name': 'Deudas aportes',
        #     },
        #     'report_type': 'xlsx',
        # }

