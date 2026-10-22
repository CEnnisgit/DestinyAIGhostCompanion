import { execFileSync } from 'node:child_process';
const url = new URL(process.env.VITE_API_URL || 'invalid');
if (url.protocol !== 'https:') throw new Error('VITE_API_URL must be an HTTPS hosted server URL');
execFileSync('npm', ['run', 'build'], { stdio: 'inherit' });
