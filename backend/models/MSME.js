const mongoose = require('mongoose');

const msmeSchema = new mongoose.Schema({
    owner: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    businessName: {
        type: String,
        required: true
    },
    registrationNumber: {
        type: String,
        required: true,
        unique: true
    },
    category: {
        type: String,
        enum: ['Micro', 'Small', 'Medium'],
        required: true
    },
    industry: String,
    annualTurnover: Number,
    employeeCount: Number,
    address: {
        street: String,
        city: String,
        state: String,
        pincode: String
    },
    blockchainId: Number,
    creditScore: {
        type: Number,
        default: 0
    },
    isVerified: {
        type: Boolean,
        default: false
    },
    createdAt: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('MSME', msmeSchema);