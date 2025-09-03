# models/performance_yield_account_line.py
from odoo import models, fields, api

class PerformanceYieldAccountLine(models.Model):
    _name = 'performance.yield.account.line'
    _description = 'Línea de rendimiento por cuenta contable'
    _order = 'account_id'

    batch_id = fields.Many2one('performance.yield.batch', required=True, ondelete='cascade')
    currency_id = fields.Many2one(related='batch_id.currency_id', store=True, readonly=True)

    account_id = fields.Many2one('account.account', string='Cuenta contable', required=True, index=True)

    debit = fields.Monetary(string='Debe', currency_field='currency_id', compute='_compute_amounts', store=True)
    credit = fields.Monetary(string='Haber', currency_field='currency_id', compute='_compute_amounts', store=True)
    balance = fields.Monetary(string='Saldo (Debe-Haber)', currency_field='currency_id',
                              compute='_compute_amounts', store=True)

    @api.depends('account_id', 'batch_id.date_start', 'batch_id.date_end')
    def _compute_amounts(self):
        """Usa read_group en account.move.line para sumar por cuenta y rango de fechas (asientos posteados)."""
        # Agrupar por account_id con dominio por fechas
        # Construimos por batch para minimizar queries
        lines_by_batch = {}
        for line in self:
            lines_by_batch.setdefault(line.batch_id.id, set()).add(line.account_id.id)

        # Traer sumas por cada batch en un solo read_group
        for batch_id, account_ids in lines_by_batch.items():
            batch = self.env['performance.yield.batch'].browse(batch_id)
            if not batch.date_start or not batch.date_end or not account_ids:
                # si faltan datos, poner 0s
                for l in self.filtered(lambda x: x.batch_id.id == batch_id):
                    l.debit = l.credit = l.balance = 0.0
                continue

            domain = [
                ('account_id', 'in', list(account_ids)),
                ('date', '>=', batch.date_start),
                ('date', '<=', batch.date_end),
                ('parent_state', '=', 'posted'),  # solo asientos contabilizados
            ]
            grouped = self.env['account.move.line'].read_group(
                domain=domain,
                fields=['account_id', 'debit:sum', 'credit:sum', 'balance:sum'],
                groupby=['account_id'],
                lazy=False
            )
            # Mapear resultados por cuenta
            sums = {g['account_id'][0]: g for g in grouped}

            for l in self.filtered(lambda x: x.batch_id.id == batch_id):
                g = sums.get(l.account_id.id)
                l.debit = g.get('debit', 0.0) if g else 0.0
                l.credit = g.get('credit', 0.0) if g else 0.0
                # balance en AML = debit - credit (en Odoo estándar)
                l.balance = g.get('balance', l.debit - l.credit) if g else 0.0

    # Método útil para el botón del padre
    def _recompute_from_parent_dates(self):
        for line in self:
            # forzar recompute tocando campos dependientes
            line._compute_amounts()
