import { config } from "dotenv";
import { drizzle } from "drizzle-orm/better-sqlite3";
import { migrate } from "drizzle-orm/better-sqlite3/migrator";
import Database from "better-sqlite3";
import { join } from "path";
import { mkdirSync } from "fs";

config({
  path: ".env.local",
});

const runMigrate = async () => {
  // Ensure data directory exists
  const dataDir = join(process.cwd(), "data");
  try {
    mkdirSync(dataDir, { recursive: true });
  } catch {
    // Directory may already exist
  }

  const dbPath = join(dataDir, "chat.db");
  console.log(`📁 Using SQLite database at: ${dbPath}`);

  const sqlite = new Database(dbPath);

  // Migration helper: Ensure 'parts' column exists on 'message' table if table was created by an older version
  try {
    const tableInfo = sqlite.pragma("table_info(message)") as Array<{ name: string }>;
    if (tableInfo.length > 0 && !tableInfo.some((col) => col.name === "parts")) {
      sqlite.exec("ALTER TABLE message ADD COLUMN parts TEXT;");
    }
  } catch {
    // Table may not exist yet for fresh databases
  }

  const db = drizzle(sqlite);

  console.log("⏳ Running migrations...");

  const start = Date.now();
  migrate(db, { migrationsFolder: "./lib/db/migrations" });
  const end = Date.now();

  console.log("✅ Migrations completed in", end - start, "ms");

  sqlite.close();
  process.exit(0);
};

runMigrate().catch((err) => {
  console.error("❌ Migration failed");
  console.error(err);
  process.exit(1);
});
