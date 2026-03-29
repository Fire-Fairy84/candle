import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { TradingPair } from "@/lib/types";

interface PairCardProps {
  pair: TradingPair;
}

export function PairCard({ pair }: PairCardProps) {
  return (
    <Link href={`/pairs/${pair.id}`}>
      <Card className="hover:bg-accent transition-colors cursor-pointer h-full">
        <CardHeader className="pb-2">
          <CardTitle className="text-base">{pair.symbol}</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Badge variant="secondary">{pair.exchange.slug}</Badge>
          <Badge variant="outline">{pair.timeframe}</Badge>
        </CardContent>
      </Card>
    </Link>
  );
}
