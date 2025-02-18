from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import re
from dateutil.relativedelta import relativedelta


class WizardReportAll(models.TransientModel):
    _name = 'wizard.report.all'

    date_start = fields.Date(string='Fecha de inicio', required=True)
    date_end = fields.Date(string='Fecha de fin', required=True)
    type_report = fields.Selection([('aportes', 'Aportes'),
                                    ('prestamos', 'Prestamos')],
                                   string='Tipo de reporte', required=True)

    def action_generate_report(self):
        if self.type_report == 'aportes':
            return self.env.ref('rod_cooperativa_aportes.action_report_contributions').report_action(self)
        elif self.type_report == 'prestamos':
            return self.env.ref('rod_cooperativa.action_report_loans').report_action(self)
        else:
            raise ValidationError('Debe seleccionar un tipo de reporte')