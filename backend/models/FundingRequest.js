const mongoose = require('mongoose');

const fundingRequestSchema = new mongoose.Schema({
    msme: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'MSME',
        required: true
    },
    owner: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    amountRequired: {
        type: Number,
        required: true
    },
    amountFunded: {
        type: Number,
        default: 0
    },
    interestRate: {
        type: Number,
        required: true
    },
    tenure: {
        type: Number,
        required: true
    },
    purpose: {
        type: String,
        required: true
    },
    description: String,
    status: {
        type: String,
        enum: ['pending', 'approved', 'funded', 'repaying', 'completed', 'rejected'],
        default: 'pending'
    },
    blockchainRequestId: Number,
    investments: [{
        investor: {
            type: mongoose.Schema.Types.ObjectId,
            ref: 'User'
        },
        amount: Number,
        transactionHash: String,
        investedAt: Date
    }],
    createdAt: {
        type: Date,
        default: Date.now
    }
});

module.exports = mongoose.model('FundingRequest', fundingRequestSchema);