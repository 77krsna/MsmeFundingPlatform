require('dotenv').config();
const { Sequelize } = require('sequelize');

const sequelize = new Sequelize(process.env.DATABASE_URL, {
    dialect: 'postgres',
    logging: false,
});

const connectDB = async () => {
    try {
        await sequelize.authenticate();
        console.log('✅ PostgreSQL Connected to msme_finance');
        console.log('✅ Using existing database schema');
    } catch (error) {
        console.error('❌ PostgreSQL Error:', error.message);
        console.log('⚠️  Server will continue without database...');
    }
};

module.exports = { sequelize, connectDB };