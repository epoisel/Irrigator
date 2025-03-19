'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function ControlPage() {
  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Irrigation Control</h1>
      <Card>
        <CardHeader>
          <CardTitle>Manual Control</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Control panel coming soon...
          </p>
        </CardContent>
      </Card>
    </div>
  );
} 