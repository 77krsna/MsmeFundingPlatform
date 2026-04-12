require('dotenv').config();
const { Client } = require('pg');

const seed = async () => {
    const client = new Client({
        connectionString: process.env.DATABASE_URL
    });

    try {
        await client.connect();
        console.log('🌱 Seeding database...\n');

        // Add MSMEs
        await client.query(`
            INSERT INTO msmes (name, gstin, wallet_address, business_type, annual_revenue, credit_score, verified, created_at)
            VALUES 
            ('ABC Manufacturing Pvt Ltd', '29ABCDE1234F1Z5', '0x1234567890123456789012345678901234567890', 'Manufacturing', 5000000, 750, true, NOW()),
            ('XYZ Tech Solutions', '27XYZDE5678G2Z6', '0x2345678901234567890123456789012345678901', 'Technology', 3000000, 680, true, NOW()),
            ('PQR Exports Ltd', '19PQRDE9012H3Z7', '0x3456789012345678901234567890123456789012', 'Export', 8000000, 720, true, NOW())
            ON CONFLICT DO NOTHING;
        `);
        console.log('✅ Added 3 MSMEs');

        // Add GEM Orders
        await client.query(`
            INSERT INTO gem_orders (gem_number, buyer_name, item_description, quantity, total_value, bid_end_date, status, created_at)
            VALUES 
            ('GEM/2024/B/001', 'Ministry of Defence', 'Office Furniture', 100, 2500000, NOW() + INTERVAL '30 days', 'active', NOW()),
            ('GEM/2024/B/002', 'Railway Board', 'Computer Equipment', 50, 3500000, NOW() + INTERVAL '45 days', 'active', NOW()),
            ('GEM/2024/B/003', 'BSNL', 'Networking Hardware', 200, 5000000, NOW() + INTERVAL '60 days', 'active', NOW()),
            ('GEM/2024/B/004', 'Indian Army', 'Safety Equipment', 150, 1800000, NOW() + INTERVAL '20 days', 'active', NOW())
            ON CONFLICT DO NOTHING;
        `);
        console.log('✅ Added 4 GEM Orders');

        // Add Investors
        await client.query(`
            INSERT INTO investors (name, wallet_address, email, total_invested, active_investments, kyc_verified, created_at)
            VALUES 
            ('Investor Alpha', '0x4567890123456789012345678901234567890123', 'alpha@investor.com', 10000000, 5, true, NOW()),
            ('Investor Beta', '0x5678901234567890123456789012345678901234', 'beta@investor.com', 7500000, 3, true, NOW()),
            ('Investor Gamma', '0x6789012345678901234567890123456789012345', 'gamma@investor.com', 5000000, 2, true, NOW())
            ON CONFLICT DO NOTHING;
        `);
        console.log('✅ Added 3 Investors');

        console.log('\n🎉 Database seeded successfully!');
    } catch (error) {
        console.error('❌ Seeding error:', error.message);
    } finally {
        await client.end();
    }
};

seed();