interface Version {
  version: string;
  releaseDate: string;
  deprecated: boolean;
  sunsetDate?: string;
  breakingChanges: string[];
  migrationGuide?: string;
}

interface DeprecationRequest {
  version: string;
  sunsetDate: string;
  migrationGuide: string;
}

interface APIResponse {
  success: boolean;
  data?: any;
  error?: string;
  warning?: string;
}

class VersionManager {
  private versions: Map<string, Version> = new Map();
  private changelog: string[] = [];

  constructor() {
    this.initializeDefaultVersions();
  }

  private initializeDefaultVersions() {
    const defaultVersions: Version[] = [
      {
        version: "1.0.0",
        releaseDate: "2024-01-15",
        deprecated: false,
        breakingChanges: ["Initial release"],
      },
      {
        version: "1.1.0",
        releaseDate: "2024-02-20",
        deprecated: false,
        breakingChanges: ["Added pagination to list endpoints"],
      },
      {
        version: "2.0.0",
        releaseDate: "2024-03-10",
        deprecated: false,
        breakingChanges: ["Removed legacy authentication", "Changed response format for /users"],
        migrationGuide: "/api/migrate/2.0.0",
      },
    ];

    defaultVersions.forEach(v => this.versions.set(v.version, v));
    this.changelog.push("Initialized with default API versions");
  }

  getAllVersions(): Version[] {
    return Array.from(this.versions.values()).sort((a, b) => 
      this.compareVersions(b.version, a.version)
    );
  }

  getVersion(version: string): Version | undefined {
    return this.versions.get(version);
  }

  deprecateVersion(version: string, sunsetDate: string, migrationGuide: string): boolean {
    const existing = this.versions.get(version);
    if (!existing) return false;

    existing.deprecated = true;
    existing.sunsetDate = sunsetDate;
    existing.migrationGuide = migrationGuide;
    
    this.changelog.push(`Deprecated version ${version} with sunset date ${sunsetDate}`);
    return true;
  }

  private compareVersions(a: string, b: string): number {
    const aParts = a.split('.').map(Number);
    const bParts = b.split('.').map(Number);
    
    for (let i = 0; i < 3; i++) {
      if (aParts[i] !== bParts[i]) {
        return aParts[i] - bParts[i];
      }
    }
    return 0;
  }

  getChangelog(): string[] {
    return [...this.changelog];
  }

  negotiateVersion(requested: string): Version | undefined {
    const requestedParts = requested.split('.').map(Number);
    
    return this.getAllVersions()
      .filter(v => !v.deprecated)
      .reduce((best, current) => {
        const currentParts = current.version.split('.').map(Number);
        
        if (currentParts[0] !== requestedParts[0]) return best;
        if (currentParts[1] > requestedParts[1]) return best;
        
        return !best || this.compareVersions(current.version, best.version) > 0 ? current : best;
      }, undefined as Version | undefined);
  }
}

const versionManager = new VersionManager();

const HTML_TEMPLATE = (content: string, title: string = "API Versioner") => `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --dark: #0a0a0f;
            --accent: #0284c7;
            --light: #f8fafc;
            --gray: #64748b;
            --border: #1e293b;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--dark);
            color: var(--light);
            line-height: 1.6;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            border-bottom: 1px solid var(--border);
            padding-bottom: 2rem;
            margin-bottom: 3rem;
        }
        
        h1 {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent), #0ea5e9);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            color: var(--gray);
            font-size: 1.25rem;
            font-weight: 300;
        }
        
        .content {
            display: grid;
            gap: 2rem;
        }
        
        .card {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
        }
        
        .card h2 {
            color: var(--accent);
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }
        
        .version-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: var(--accent);
            color: white;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
        }
        
        .deprecated {
            background: #dc2626;
        }
        
        .warning {
            background: #d97706;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            border-left: 4px solid #f59e0b;
        }
        
        footer {
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border);
            text-align: center;
            color: var(--gray);
            font-size: 0.875rem;
        }
        
        .fleet {
            color: var(--accent);
            font-weight: 600;
        }
        
        code {
            background: rgba(0, 0, 0, 0.3);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.875rem;
        }
        
        pre {
            background: rgba(0, 0, 0, 0.3);
            padding: 1rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
        }
        
        .endpoint {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
        }
        
        .method {
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.875rem;
        }
        
        .get { background: #10b981; color: white; }
        .post { background: #f59e0b; color: white; }
        
        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }
            
            h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>API Versioner</h1>
            <p class="subtitle">Breaking changes without breaking things</p>
        </header>
        
        <div class="content">
            ${content}
        </div>
        
        <footer>
            <p>Powered by <span class="fleet">Fleet</span> • Semantic versioning, deprecation warnings, migration guides</p>
            <p style="margin-top: 0.5rem;">
                <a href="/health" style="color: var(--accent); text-decoration: none;">Health Check</a> • 
                <a href="/api/versions" style="color: var(--accent); text-decoration: none;">API Versions</a>
            </p>
        </footer>
    </div>
</body>
</html>
`;

const renderVersionsPage = (versions: Version[]) => {
  const versionCards = versions.map(v => `
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: start;">
        <div>
          <span class="version-badge ${v.deprecated ? 'deprecated' : ''}">v${v.version}</span>
          <span style="color: var(--gray); font-size: 0.875rem;">Released: ${v.releaseDate}</span>
        </div>
        ${v.deprecated ? 
          `<div class="warning">
            <strong>Deprecated</strong>${v.sunsetDate ? ` • Sunset: ${v.sunsetDate}` : ''}
          </div>` : ''
        }
      </div>
      
      <h2>Breaking Changes</h2>
      <ul style="margin-left: 1.5rem; margin-bottom: 1rem;">
        ${v.breakingChanges.map(change => `<li>${change}</li>`).join('')}
      </ul>
      
      ${v.migrationGuide ? `
        <div style="margin-top: 1rem;">
          <a href="${v.migrationGuide}" style="color: var(--accent); text-decoration: none;">
            → View Migration Guide
          </a>
        </div>
      ` : ''}
    </div>
  `).join('');

  return HTML_TEMPLATE(`
    <div class="card">
      <h2>API Endpoints</h2>
      <div class="endpoint">
        <span class="method get">GET</span>
        <code>/api/versions</code>
        <span>List all API versions</span>
      </div>
      <div class="endpoint">
        <span class="method post">POST</span>
        <code>/api/deprecate</code>
        <span>Deprecate a version</span>
      </div>
      <div class="endpoint">
        <span class="method get">GET</span>
        <code>/api/migrate/:version</code>
        <span>Get migration guide</span>
      </div>
    </div>
    
    <div class="card">
      <h2>Available Versions</h2>
      ${versionCards}
    </div>
    
    <div class="card">
      <h2>Version Negotiation</h2>
      <p>Specify your API version using the <code>Accept-Version</code> header:</p>
      <pre>Accept-Version: 1.x</pre>
      <p>The system will automatically serve the latest compatible version.</p>
    </div>
  `, "API Versions");
};

const renderMigrationGuide = (version: Version) => {
  return HTML_TEMPLATE(`
    <div class="card">
      <h2>Migration Guide for v${version.version}</h2>
      <div style="margin-bottom: 1rem;">
        <span class="version-badge">v${version.version}</span>
        <span style="color: var(--gray);">Released: ${version.releaseDate}</span>
      </div>
      
      <h3>Breaking Changes</h3>
      <ul style="margin-left: 1.5rem; margin-bottom: 2rem;">
        ${version.breakingChanges.map(change => `<li>${change}</li>`).join('')}
      </ul>
      
      <h3>Migration Steps</h3>
      <div style="background: rgba(2, 132, 199, 0.1); padding: 1.5rem; border-radius: 8px; border-left: 4px solid var(--accent);">
        <p>To migrate to v${version.version}:</p>
        <ol style="margin-left: 1.5rem; margin-top: 1rem;">
          <li>Update your API client to use version ${version.version}</li>
          <li>Review all breaking changes listed above</li>
          <li>Test your integration thoroughly</li>
          <li>Update any deprecated endpoints or parameters</li>
          <li>Monitor for any issues after deployment</li>
        </ol>
      </div>
      
      ${version.deprecated && version.sunsetDate ? `
        <div class="warning" style="margin-top: 2rem;">
          <strong>⚠️ This version is deprecated</strong>
          <p>Support ends on ${version.sunsetDate}. Please migrate to a newer version.</p>
        </div>
      ` : ''}
      
      <div style="margin-top: 2rem;">
        <a href="/api/versions" style="color: var(--accent); text-decoration: none;">
          ← Back to all versions
        </a>
      </div>
    </div>
  `, `Migration Guide v${version.version}`);
};

const handleRequest = async (request: Request): Promise<Response> => {
  const url = new URL(request.url);
  const path = url.pathname;

  // Set security headers
  const headers = new Headers({
    "Content-Type": "text/html",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'",
    "X-Content-Type-Options": "nosniff",
  });

  // Health check endpoint
  if (path === "/health") {
    return new Response(JSON.stringify({ status: "ok", timestamp: new Date().toISOString() }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  }

  // API endpoints
  if (path === "/api/versions") {
    if (request.method === "GET") {
      const acceptVersion = request.headers.get("Accept-Version");
      let responseData: APIResponse;

      if (acceptVersion) {
        const negotiated = versionManager.negotiateVersion(acceptVersion);
        if (negotiated) {
          responseData = {
            success: true,
            data: negotiated,
            warning: negotiated.deprecated ? `Version ${negotiated.version} is deprecated` : undefined,
          };
        } else {
          responseData = {
            success: false,
            error: `No compatible version found for ${acceptVersion}`,
          };
        }
      } else {
        responseData = {
          success: true,
          data: versionManager.getAllVersions(),
        };
      }

      return new Response(JSON.stringify(responseData), {
        status: responseData.success ? 200 : 404,
        headers: { "Content-Type": "application/json" },
      });
    }
  }

  if (path === "/api/deprecate") {
    if (request.method === "POST") {
      try {
        const body: DeprecationRequest = await request.json();
        
        if (!body.version || !body.sunsetDate) {
          return new Response(JSON.stringify({
            success: false,
            error: "Missing required fields: version, sunsetDate",
          }), {
            status: 400,
            headers: { "Content-Type": "application/json" },
          });
        }

        const success = versionManager.deprecateVersion(
          body.version,
          body.sunsetDate,
          body.migrationGuide || `/api/migrate/${body.version}`
        );

        return new Response(JSON.stringify({
          success,
          data: success ? { version: body.version, deprecated: true } : undefined,
          error: success ? undefined : `Version ${body.version} not found`,
        }), {
          status: success ? 200 : 404,
          headers: { "Content-Type": "application/json" },
        });
      } catch {
        return new Response(JSON.stringify({
          success: false,
          error: "Invalid JSON body",
        }), {
          status: 400,
          headers: { "Content-Type": "application/json" },
        });
      }
    }
  }

  if (path.startsWith("/api/migrate/")) {
    if (request.method === "GET") {
      const version = path.split("/").pop();
      if (version) {
        const versionData = versionManager.getVersion(version);
        
        if (versionData) {
          // Return HTML page for browser, JSON for API clients
          const accept = request.headers.get("Accept") || "";
          if (accept.includes("text/html")) {
            return new Response(renderMigrationGuide(versionData), {
              status: 200,
              headers,
            });
          } else {
            return new Response(JSON.stringify({
              success: true,
              data: versionData,
            }), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            });
          }
        }
      }
      
      return new Response(JSON.stringify({
        success: false,
        error: "Version not found",
      }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      });
    }
  }

  // Root path - show HTML dashboard
  if (path === "/") {
    return new Response(renderVersionsPage(versionManager.getAllVersions()), {
      status: 200,
      headers,
    });
  }

  // 404 for unknown routes
  return new Response(
    JSON.stringify({
      success: false,
      error: "Not Found",
      endpoints: ["/", "/api/versions", "/api/deprecate", "/api/migrate/:version", "/health"],
    }),
    {
      status: 404,
      headers: { "Content-Type": "application/json" },
    }
  );
};

export default {
  async fetch(request: Request): Promise<Response> {
    return handleRequest(request);
  },
};
