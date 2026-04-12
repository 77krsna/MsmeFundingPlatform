const express = require('express');
const router = express.Router();
const { sequelize } = require('../config/db');

// Get order statistics from database
router.get('/stats/summary', async (req, res) => {
    try {
        const [results] = await sequelize.query(`
            SELECT 
                (SELECT COUNT(*) FROM gem_orders) as total_orders,
                (SELECT COALESCE(SUM(CAST(order_amount AS NUMERIC)), 0) FROM gem_orders) as total_volume,
                (SELECT COUNT(*) FROM msmes) as total_msmes,
                (SELECT COUNT(*) FROM investors) as total_investors
        `);

        const stats = results[0];
        
        // Calculate additional stats
        stats.active_orders = parseInt(stats.total_orders);
        stats.funded_orders = 0;
        stats.average_order_value = parseInt(stats.total_orders) > 0 
            ? parseFloat(stats.total_volume) / parseInt(stats.total_orders)
            : 0;

        // Convert BigInt to Number for JSON
        Object.keys(stats).forEach(key => {
            if (typeof stats[key] === 'bigint') {
                stats[key] = Number(stats[key]);
            }
        });

        res.json(stats);
    } catch (error) {
        console.error('Stats error:', error.message);
        res.status(500).json({ success: false, message: error.message });
    }
});

// Get all orders from database
router.get('/', async (req, res) => {
    try {
        const [orders] = await sequelize.query(`
            SELECT 
                id,
                gem_order_id,
                order_amount,
                order_date,
                delivery_deadline,
                buyer_organization,
                product_category,
                status,
                created_at
            FROM gem_orders 
            ORDER BY created_at DESC 
            LIMIT 50
        `);

        res.json({
            success: true,
            orders: orders,
            total: orders.length
        });
    } catch (error) {
        console.error('Orders error:', error.message);
        res.status(500).json({ success: false, message: error.message });
    }
});

// Get order by ID
router.get('/:id', async (req, res) => {
    try {
        const [orders] = await sequelize.query(`
            SELECT * FROM gem_orders 
            WHERE id = :id OR gem_order_id = :id
            LIMIT 1
        `, {
            replacements: { id: req.params.id }
        });

        if (orders.length > 0) {
            res.json({ success: true, order: orders[0] });
        } else {
            res.status(404).json({ success: false, message: 'Order not found' });
        }
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

module.exports = router;