from odoo import api, fields, models


class StockSenseCategory(models.Model):
    _name = 'stocksense.category'
    _description = 'StockSense Product Category'
    _order = 'name'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    product_count = fields.Integer(compute='_compute_product_count')

    def _compute_product_count(self):
        Product = self.env['stocksense.product']
        for rec in self:
            rec.product_count = Product.search_count([
                ('category_id', '=', rec.id)
            ])


class StockSenseProduct(models.Model):
    _name = 'stocksense.product'
    _description = 'StockSense Product'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    sku = fields.Char(string='SKU / Code', required=True, index=True)
    category_id = fields.Many2one(
        'stocksense.category',
        string='Category',
        ondelete='set null'
    )
    uom = fields.Char(string='Unit of Measure', default='Units', required=True)
    initial_stock = fields.Float(string='Initial Stock', default=0.0)
    reorder_level = fields.Float(string='Reorder Level', default=10.0)
    current_stock = fields.Float(
        string='Current Stock',
        compute='_compute_current_stock'
    )
    low_stock = fields.Boolean(
        string='Low Stock',
        compute='_compute_low_stock'
    )
    out_of_stock = fields.Boolean(
        string='Out of Stock',
        compute='_compute_low_stock'
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('sku_unique', 'unique(sku)', 'SKU / Code must be unique.')
    ]

    @api.depends('initial_stock')
    def _compute_current_stock(self):
        Ledger = self.env['stocksense.ledger']
        for product in self:
            changes = Ledger.search([
                ('product_id', '=', product.id)
            ]).mapped('quantity_change')
            product.current_stock = product.initial_stock + sum(changes)

    @api.depends('current_stock', 'reorder_level')
    def _compute_low_stock(self):
        for product in self:
            product.low_stock = (
                product.current_stock > 0 and
                product.current_stock <= product.reorder_level
            )
            product.out_of_stock = product.current_stock <= 0
