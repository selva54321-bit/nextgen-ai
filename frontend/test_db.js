import pg from 'pg';
const { Client } = pg;

const client = new Client({
  connectionString: 'postgresql://postgres.rgkngmdpoylnupcebqlf:HarishSathiya@07@aws-0-ap-south-1.pooler.supabase.com:5432/postgres'
});

async function run() {
  await client.connect();
  const res = await client.query('SELECT * FROM orders');
  console.log('Total orders:', res.rows.length);
  if (res.rows.length > 0) {
    console.log(res.rows.slice(0, 5));
  }
  await client.end();
}

run().catch(console.error);
