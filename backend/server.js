const express = require('express');
const dotenv = require('dotenv');
const cors = require('cors');
const { connectDB } = require('./config/db');

// Load environment variables
dotenv.config();

// Initialize express
const app = express();

// Connect to database (non-blocking)
connectDB();

// Middleware
app.use(cors({
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Basic Routes
app.get('/', (req, res) => {
    res.json({
        message: '🚀 MSME Blockchain Funding Platform API',
        version: '1.0.0',
        status: 'Running',
        endpoints: {
            health: '/health',
            status: '/status',
            auth: '/api/auth',
            msme: '/api/msme',
            funding: '/api/funding',
            admin: '/api/admin'
        }
    });
});

app.get('/health', (req, res) => {
    res.json({
        status: 'OK',
        timestamp: new Date().toISOString(),
        services: {
            api: 'running',
            database: 'disconnected'
        }
    });
});

app.get('/status', (req, res) => {
    res.json({
        status: 'operational',
        uptime: process.uptime(),
        timestamp: new Date().toISOString()
    });
});

// API Routes - Only load if files exist
// API Routes - Only load if files exist
// API Routes
try {
    app.use('/api/auth', require('./routes/authRoutes'));
    app.use('/api/orders', require('./routes/orderRoutes'));
    console.log('✅ API routes loaded');
} catch (error) {
    console.log('⚠️  Routes error:', error.message);
}

// Error handling
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        success: false,
        message: err.message
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        success: false,
        message: 'Route not found'
    });
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
    console.log('\n' + '='.repeat(60));
    console.log(`🚀 MSME Backend Server Running`);
    console.log(`📍 Port: ${PORT}`);
    console.log(`🌐 URL: http://localhost:${PORT}`);
    console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
    console.log('='.repeat(60) + '\n');
});