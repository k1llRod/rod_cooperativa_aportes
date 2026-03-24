from odoo import models, fields, api, _
from num2words import num2words
from odoo.exceptions import UserError


class FinalizeContributions(models.Model):
    _name = 'finalize.contributions'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Codigo')
    # 1. Definir la moneda primero
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one('res.currency', string='Moneda (Bs)', related='company_id.currency_id', readonly=True)

    liquidation = fields.Boolean(string='Liquidar prestamo', default=False)
    liquidation_contributions = fields.Boolean(string="Liquidar aportes", default=False)
    date_proccess = fields.Date(string='Fecha de proceso')
    partner_payroll_ids = fields.Many2one('partner.payroll', string='Aportes')
    loan_application_ids = fields.Many2one('loan.application', string='Prestamo')
    disengagement = fields.Float('Desvinculacion')
    regulation_cup = fields.Float('Tasa de regulacion')
    total_mandatory_contributions = fields.Float(string='Total de aportes obligatorios', digits=(16, 2))
    total_voluntary_contributions = fields.Float(string='Total de aportes voluntarios', digits=(16, 2))
    total_capital_initial = fields.Float('Total capital inicial', digits=(16, 2))
    total_voluntary = fields.Float('Total aportes voluntarios', compute='calculate_total_voluntary', digits=(16, 2))
    total_amount = fields.Float(string='Total Debe', compute='calculate_total_amount', digits=(16, 2))
    total_amount_credit = fields.Float(string='Total Haber', compute='calculate_amount_credit', digits=(16, 2))
    manual_regulation_cup = fields.Float(string="Tasa de regulacion manual", digits=(16, 2))
    manual_post_mortem = fields.Float(string="Post mortem manual", digits=(16, 2))
    manual_aporte_obligatorio = fields.Float(string="Aporte obligatorio manual", digits=(16, 2))
    manual_aporte_voluntario = fields.Float(string="Aporte voluntario manual CAT 'A'", digits=(16, 2))
    rest_contributions = fields.Float(string="Monto restante aportes", compute='calculate_rest_contributions',
                                      digits=(16, 2))
    other_contributions = fields.Float('Total otros aportes', digits=(16, 2))
    surpluses = fields.Float('Total excedentes', digits=(16, 2))
    perfomance_contributions = fields.Float('Total rendimiento', digits=(16, 2))

    total_diference_contribution_loan = fields.Float(string='Diferencia aportes - prestamo',
                                                     compute='calculate_diference_contribution_loan', digits=(16, 2))
    total_partial_devolution = fields.Float(string="Devolucion parcial")
    state = fields.Selection([('draft', 'Borrador'),
                              ('done', 'Confirmado')],
                             string='Estado', default='draft')

    loan_capital_bolivianos = fields.Float(string='Total capital prestamo', digits=(16, 2))
    balance_interest_month_bolivianos = fields.Float(string='Total dias de interes', digits=(16, 2))

    # Debes usar Monetary porque el origen en loan.application es Monetary
    loan_capital_bolivianos_related = fields.Monetary(
        string='Total capital prestamo relacionado',
        related='loan_application_ids.balance_capital_bs',
        currency_field='currency_id',  # Requerido para campos Monetary
        readonly=True
    )

    balance_interest_month_bolivianos_related = fields.Monetary(
        string='Total dias de interes relacionado',
        related='loan_application_ids.balance_total_interest_month_bs',
        currency_field='currency_id',  # Requerido para campos Monetary
        readonly=True
    )

    discount_contribution = fields.Float(string='Descuento aporte', digits=(16, 2))



    journal_id = fields.Many2one('account.journal', string='Diario')
    account_move_id = fields.Many2one('account.move', string='Asiento contable')
    account_voluntary_contributions = fields.Many2one('account.account', string='Cuenta Aportes voluntarios')
    account_mandatory_contributions = fields.Many2one('account.account', string='Cuenta Aportes Obligatorios')
    account_other_contributions = fields.Many2one('account.account', string='Cuenta Otros aportes')
    account_surpluses = fields.Many2one('account.account', string='Cuenta Excedentes')
    account_performance_contributions = fields.Many2one('account.account', string='Rendimiento')

    account_capital_loan = fields.Many2one('account.account', string='Cuenta Capital credito')
    account_interest_month = fields.Many2one('account.account', string='Cuenta Interes mensual')
    account_bank_rest = fields.Many2one('account.account', string='Cuenta Banco saldo restante')

    account_disengagement = fields.Many2one('account.account', string='Cuenta de desvinculacion')
    account_regulation_cup = fields.Many2one('account.account', string='Cuenta tasa de regulacion')
    account_bank_rest_contributions = fields.Many2one('account.account', string='Cuenta Banco aportes restantes')
    account_manual_post_mortem = fields.Many2one('account.account', string='Cuenta Post mortem manual')
    account_manual_aporte_obligatorio = fields.Many2one('account.account', string='Cuenta Aporte obligatorio manual')

    account_manual_aporte_voluntario = fields.Many2one('account.account', string='Cuenta Aporte voluntario manual CAT "A"')

    literal_number = fields.Char(string='Amount literal', compute='_compute_literal_number')
    literal_res_contributions = fields.Char(string='Amount literal rest contributions', compute='_compute_literal_res_contributions')

    @api.depends('total_voluntary_contributions', 'total_capital_initial')
    def calculate_total_voluntary(self):
        for record in self:
            total = record.total_voluntary_contributions + record.total_capital_initial
            record.total_voluntary = total

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('finalize.contributions')
        vals['name'] = name
        res = super(FinalizeContributions, self).create(vals)
        return res

    def open_finalize_contributions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Liquidacion de aportes'),
            'res_model': 'finalize.contributions',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    @api.depends('discount_contribution', 'loan_capital_bolivianos', 'balance_interest_month_bolivianos')
    def calculate_diference_contribution_loan(self):
        for record in self:
            if record.liquidation == True and record.liquidation_contributions == True:
                total_loan = record.loan_capital_bolivianos + record.balance_interest_month_bolivianos
                record.total_diference_contribution_loan = record.total_amount - total_loan
            else:
                total_loan = record.loan_capital_bolivianos + record.balance_interest_month_bolivianos
                record.total_diference_contribution_loan = record.discount_contribution - total_loan

    @api.depends('total_voluntary_contributions', 'total_capital_initial', 'other_contributions', 'surpluses',
                 'perfomance_contributions', 'total_mandatory_contributions')
    def calculate_total_amount(self):
        for record in self:
            total = record.total_voluntary_contributions + record.total_capital_initial + record.other_contributions + record.surpluses + record.perfomance_contributions + record.total_mandatory_contributions
            record.total_amount = total

    @api.depends('disengagement', 'manual_regulation_cup', 'rest_contributions')
    def calculate_amount_credit(self):
        for record in self:
            record.total_amount_credit = (record.disengagement + record.manual_regulation_cup +
                                          record.rest_contributions + record.loan_capital_bolivianos +
                                          record.balance_interest_month_bolivianos + record.manual_post_mortem +
                                          record.manual_aporte_obligatorio + record.manual_aporte_voluntario)

    @api.depends('manual_regulation_cup', 'disengagement','manual_post_mortem', 'manual_aporte_obligatorio', 'manual_aporte_voluntario')
    def calculate_rest_contributions(self):
        for record in self:
            if record.total_partial_devolution > 0:
                record.rest_contributions = record.total_partial_devolution
            else:
                record.rest_contributions = (record.total_amount - record.disengagement - record.manual_regulation_cup -
                                             record.loan_capital_bolivianos - record.balance_interest_month_bolivianos -
                                             record.manual_post_mortem - record.manual_aporte_obligatorio - record.manual_aporte_voluntario)

    def action_confirm(self):
        for record in self:
            if record.partner_payroll_ids.state != 'process':
                raise UserError(_("Los aportes deben estar en estado 'Proceso'."))

            # 1. Sincronización de montos (Evitar escrituras innecesarias con condicionales)
            p_ids = record.partner_payroll_ids
            sync_vals = {
                'total_mandatory_contributions': p_ids.mandatory_contribution_certificate_total,
                'total_voluntary_contributions': p_ids.voluntary_contribution_certificate_total,
                'total_capital_initial': p_ids.capital_initial,
                'other_contributions': p_ids.other_contribution_total,
                'surpluses': p_ids.surpluses_total,
                'loan_capital_bolivianos': record.loan_application_ids.balance_capital_bs,
                'balance_interest_month_bolivianos': record.loan_application_ids.balance_total_interest_month_bs,
            }

            # Aplicamos los valores sincronizados al record
            record.write(sync_vals)

            # 2. Cálculo de verificación ACTUALIZADO
            # Incluimos rendimientos y los nuevos campos manuales (obligatorio y VOLUNTARIO)
            total_calc = round(
                record.total_mandatory_contributions +
                record.total_voluntary_contributions +
                record.total_capital_initial +
                record.other_contributions +
                record.surpluses +
                record.perfomance_contributions, 2  # Rendimientos
                # record.manual_aporte_obligatorio +
                # record.manual_aporte_voluntario, 2  # Campo solicitado
            )

            if round(record.total_amount, 2) != total_calc:
                raise UserError(_(
                    "El total de aportes (%s) no coincide con el total calculado (%s). "
                    "Por favor, revise los datos."
                ) % (record.total_amount, total_calc))

            # 3. Preparación de líneas contables
            move_lines = []
            partner = record.partner_payroll_ids.partner_id

            def add_line(account, debit, credit, name):
                if account and (round(debit, 2) > 0 or round(credit, 2) > 0):
                    move_lines.append((0, 0, {
                        'name': name,
                        'account_id': account.id,
                        'debit': debit,
                        'credit': credit,
                        'partner_id': partner.id if debit > 0 else False,
                    }))

            # DEBE: Liquidación de Aportes (Activos que el fondo devuelve/cruza)
            if record.liquidation_contributions:
                # Aportes Voluntarios (Suma el total calculado que ya incluye el manual)
                add_line(record.account_voluntary_contributions, record.total_voluntary, 0,
                         False)

                # Si el aporte manual tiene cuenta específica, podrías separarlo aquí,
                # pero usualmente se suma al total del rubro.
                # Si quieres que vaya a su propia cuenta 'account_manual_aporte_voluntario':
                # if record.manual_aporte_voluntario > 0:
                #     add_line(record.account_manual_aporte_voluntario, record.manual_aporte_voluntario, 0,
                #              False)

                add_line(record.account_mandatory_contributions, record.total_mandatory_contributions, 0,
                         False)
                add_line(record.account_other_contributions, record.other_contributions, 0, False)
                add_line(record.account_surpluses, record.surpluses, 0, False)
                add_line(record.account_performance_contributions, record.perfomance_contributions, 0, False)

            # HABER: Deudas o Salida de Efectivo
            if record.liquidation:
                add_line(record.account_capital_loan, 0, record.loan_capital_bolivianos, False)
                add_line(record.account_interest_month, 0, record.balance_interest_month_bolivianos,
                         False)


            add_line(record.account_disengagement, 0, record.disengagement, False)
            add_line(record.account_regulation_cup, 0, record.manual_regulation_cup, False)
            add_line(record.account_manual_post_mortem, 0, record.manual_post_mortem, False)
            add_line(record.account_manual_aporte_obligatorio, 0, record.manual_aporte_obligatorio,
                     False)
            add_line(record.account_manual_aporte_voluntario, 0, record.manual_aporte_voluntario, False)

            # Saldo a devolver al socio (Banco/Caja)
            if record.rest_contributions > 0:
                add_line(record.account_bank_rest_contributions, 0, record.rest_contributions,
                         False)

            # 4. Creación del Asiento
            move = self.env['account.move'].create({
                'date': record.date_proccess,
                'journal_id': record.journal_id.id,
                'ref': f"CERTIFICADO DEVOLUCIÓN: {partner.name}",
                'move_type': 'entry',
                'line_ids': move_lines,
            })

            # 5. Cierre y Vinculación
            record.write({
                'account_move_id': move.id,
                'state': 'done'
            })

            p_ids.write({'state': 'process_finalized'})

            if record.liquidation and record.loan_application_ids:
                record.loan_application_ids.write({'state': 'liquidation_process'})
                self.env['finalized.loan'].create({
                    'loan_application_id': record.loan_application_ids.id,
                    'date_finalize': record.date_proccess,
                    'balance_capital_bolivianos': record.loan_capital_bolivianos,
                    'state': 'draft'
                })

            return {
                'name': _('Asiento Contable'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': move.id,
            }

    @api.depends('total_amount')
    def _compute_literal_number(self):
        for record in self:
            record.literal_number = num2words(int(record.total_amount), lang='es').upper()
            decimal = str(round(record.total_amount % 1 * 100))
            record.literal_number = record.literal_number + ', CON ' + decimal + '/100 BOLIVIANOS'
    @api.depends('total_amount')
    def _compute_literal_res_contributions(self):
        for record in self:
            record.literal_res_contributions = num2words(int(record.rest_contributions), lang='es').upper()
            decimal = str(round(record.rest_contributions % 1 * 100))
            record.literal_res_contributions = record.literal_res_contributions + ', CON ' + decimal + '/100 BOLIVIANOS'


    def action_draft(self):
        for record in self:
            record.state = 'draft'
