from odoo import api, fields, models
from odoo.exceptions import UserError


class StockSenseOperation(models.Model):
    _name = 'stocksense.operation'
    _description = 'StockSense Inventory Operation'
    _order = 'date desc, id desc'

    name = fields.Char(default='New', readonly=True, copy=False)
    operation_type = fields.Selection([
        ('receipt', 'Receipt'),
        ('delivery', 'Delivery'),
        ('internal', 'Internal Transfer'),
    ], required=True, default='receipt')
    product_id = fields.Many2one(
        'stocksense.product',
        required=True,
        ondelete='restrict'
    )
    quantity = fields.Float(required=True)
    source_location_id = fields.Many2one(
        'stocksense.location',
        string='Source Location',
        ondelete='restrict'
    )
    destination_location_id = fields.Many2one(
        'stocksense.location',
        string='Destination Location',
        ondelete='restrict'
    )
    partner_name = fields.Char(string='Supplier / Customer')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting'),
        ('ready', 'Ready'),
        ('done', 'Done'),
        ('cancelled', 'Canceled'),
    ], default='draft', required=True)
    note = fields.Text()
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        readonly=True
    )

    def _check_locations(self):
        for rec in self:
            if rec.operation_type == 'internal':
                if not rec.source_location_id or not rec.destination_location_id:
                    raise UserError(
                        'Internal transfers require both source and destination locations.'
                    )
                if rec.source_location_id == rec.destination_location_id:
                    raise UserError(
                        'Source and destination locations must be different.'
                    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == 'New':
                prefix = {
                    'receipt': 'REC',
                    'delivery': 'DEL',
                    'internal': 'INT',
                }.get(rec.operation_type, 'OP')
                rec.name = f'{prefix}-{rec.id:05d}'
        return records

    def action_set_ready(self):
        self._check_locations()
        self.write({'state': 'ready'})
        return True

    def action_confirm(self):
        Ledger = self.env['stocksense.ledger']
        for rec in self:
            if rec.state == 'done':
                continue
            if rec.quantity <= 0:
                raise UserError('Quantity must be greater than zero.')

            rec._check_locations()

            if rec.operation_type == 'receipt':
                change = rec.quantity
            elif rec.operation_type == 'delivery':
                if rec.product_id.current_stock < rec.quantity:
                    raise UserError(
                        f'Not enough stock for {rec.product_id.name}. '
                        f'Available: {rec.product_id.current_stock:g}'
                    )
                change = -rec.quantity
            else:
                change = 0.0

            Ledger.create({
                'operation_id': rec.id,
                'product_id': rec.product_id.id,
                'operation_type': rec.operation_type,
                'quantity_change': change,
                'source_location_id': rec.source_location_id.id,
                'destination_location_id': rec.destination_location_id.id,
                'note': rec.note,
                'user_id': self.env.user.id,
            })

            LocationStock = self.env['stocksense.location.stock']

            if rec.operation_type == 'receipt' and rec.destination_location_id:
                balance = LocationStock.search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', '=', rec.destination_location_id.id),
                ], limit=1)
                if not balance:
                    balance = LocationStock.create({
                        'product_id': rec.product_id.id,
                        'location_id': rec.destination_location_id.id,
                    })
                balance.adjust(rec.quantity)

            elif rec.operation_type == 'delivery' and rec.source_location_id:
                balance = LocationStock.search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', '=', rec.source_location_id.id),
                ], limit=1)
                if balance:
                    balance.adjust(-rec.quantity)

            elif rec.operation_type == 'internal':
                source = LocationStock.search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', '=', rec.source_location_id.id),
                ], limit=1)
                if not source or source.quantity < rec.quantity:
                    raise UserError('Not enough stock at the selected source location.')
                destination = LocationStock.search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', '=', rec.destination_location_id.id),
                ], limit=1)
                if not destination:
                    destination = LocationStock.create({
                        'product_id': rec.product_id.id,
                        'location_id': rec.destination_location_id.id,
                    })
                source.adjust(-rec.quantity)
                destination.adjust(rec.quantity)

            rec.state = 'done'

        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True


class StockSenseLedger(models.Model):
    _name = 'stocksense.ledger'
    _description = 'StockSense Stock Ledger'
    _order = 'create_date desc, id desc'

    operation_id = fields.Many2one(
        'stocksense.operation',
        readonly=True,
        ondelete='set null'
    )
    product_id = fields.Many2one(
        'stocksense.product',
        required=True,
        readonly=True
    )
    operation_type = fields.Selection([
        ('receipt', 'Receipt'),
        ('delivery', 'Delivery'),
        ('internal', 'Internal Transfer'),
        ('adjustment', 'Adjustment'),
    ], readonly=True)
    quantity_change = fields.Float(readonly=True)
    source_location_id = fields.Many2one(
        'stocksense.location',
        readonly=True
    )
    destination_location_id = fields.Many2one(
        'stocksense.location',
        readonly=True
    )
    note = fields.Text(readonly=True)
    user_id = fields.Many2one('res.users', readonly=True)
    create_date = fields.Datetime(readonly=True)



class StockSenseLocationStock(models.Model):
    _name = 'stocksense.location.stock'
    _description = 'StockSense Stock by Location'
    _order = 'product_id, location_id'

    product_id = fields.Many2one('stocksense.product', required=True, ondelete='cascade')
    location_id = fields.Many2one('stocksense.location', required=True, ondelete='cascade')
    quantity = fields.Float(default=0.0)
    last_updated = fields.Datetime(default=fields.Datetime.now)

    _sql_constraints = [
        ('product_location_unique',
         'unique(product_id, location_id)',
         'A product can have only one balance record per location.')
    ]

    def adjust(self, amount):
        for rec in self:
            rec.quantity += amount
            rec.last_updated = fields.Datetime.now()


class StockSenseAdjustment(models.Model):
    _name = 'stocksense.adjustment'
    _description = 'StockSense Inventory Adjustment'
    _order = 'id desc'

    name = fields.Char(default='New', readonly=True, copy=False)
    product_id = fields.Many2one(
        'stocksense.product',
        required=True,
        ondelete='restrict'
    )
    location_id = fields.Many2one(
        'stocksense.location',
        string='Location',
        ondelete='restrict'
    )
    counted_quantity = fields.Float(required=True)
    recorded_quantity = fields.Float(
        compute='_compute_quantities',
        store=True
    )
    difference = fields.Float(
        compute='_compute_quantities',
        store=True
    )
    reason = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancelled', 'Canceled'),
    ], default='draft', required=True)

    @api.depends('product_id')
    def _compute_quantities(self):
        for rec in self:
            rec.recorded_quantity = rec.product_id.current_stock
            rec.difference = rec.counted_quantity - rec.recorded_quantity

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == 'New':
                rec.name = f'ADJ-{rec.id:05d}'
        return records

    def action_validate(self):
        Ledger = self.env['stocksense.ledger']
        for rec in self:
            if rec.state == 'done':
                continue
            if rec.difference == 0:
                rec.state = 'done'
                continue

            Ledger.create({
                'product_id': rec.product_id.id,
                'operation_type': 'adjustment',
                'quantity_change': rec.difference,
                'source_location_id': rec.location_id.id,
                'note': rec.reason or 'Physical stock adjustment',
                'user_id': self.env.user.id,
            })
            if rec.location_id:
                LocationStock = self.env['stocksense.location.stock']
                balance = LocationStock.search([
                    ('product_id', '=', rec.product_id.id),
                    ('location_id', '=', rec.location_id.id),
                ], limit=1)
                if not balance:
                    balance = LocationStock.create({
                        'product_id': rec.product_id.id,
                        'location_id': rec.location_id.id,
                    })
                balance.adjust(rec.difference)
            rec.state = 'done'
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        return True
