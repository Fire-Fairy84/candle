"use client";

import { useAlerts } from "@/hooks/useAlerts";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertBadge } from "./AlertBadge";

export function AlertsTable() {
  const { alerts, isLoading, error } = useAlerts();

  if (error) {
    return <p className="text-destructive text-sm">Failed to load alerts.</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Time</TableHead>
          <TableHead>Symbol</TableHead>
          <TableHead>Exchange</TableHead>
          <TableHead>Timeframe</TableHead>
          <TableHead>Rule</TableHead>
          <TableHead>Message</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {isLoading
          ? Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={i}>
                {Array.from({ length: 7 }).map((_, j) => (
                  <TableCell key={j}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                ))}
              </TableRow>
            ))
          : alerts.map((alert) => (
              <TableRow key={alert.id}>
                <TableCell className="text-muted-foreground text-xs whitespace-nowrap">
                  {new Date(alert.triggered_at).toLocaleString()}
                </TableCell>
                <TableCell className="font-medium">{alert.symbol}</TableCell>
                <TableCell>{alert.exchange_slug}</TableCell>
                <TableCell>{alert.timeframe}</TableCell>
                <TableCell>{alert.rule_name}</TableCell>
                <TableCell className="max-w-xs truncate text-sm text-muted-foreground">
                  {alert.message}
                </TableCell>
                <TableCell>
                  <AlertBadge sent={alert.sent} />
                </TableCell>
              </TableRow>
            ))}
        {!isLoading && alerts.length === 0 && (
          <TableRow>
            <TableCell colSpan={7} className="text-center text-muted-foreground">
              No alerts yet.
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
