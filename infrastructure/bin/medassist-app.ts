#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { MedAssistStack } from '../lib/medassist-stack';

const app = new cdk.App();

new MedAssistStack(app, 'MedAssistStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'MedAssist AI System - Medical document analysis with AWS Generative AI',
});

app.synth();
