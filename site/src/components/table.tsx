import { useEffect, useMemo } from 'react';
import { flexRender, getCoreRowModel, getPaginationRowModel, useReactTable } from '@tanstack/react-table';
import { format } from 'date-fns';
import { useQueries, useSelectedQuery } from '@lib/state/query';
import { cn } from '@lib/utils';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@components/ui/table';
import { Button } from '@components/ui/button';
import { Badge } from '@components/ui/badge';
import { QUERY_COMPLETE, FETCH_INCOMPLETE, CLEAN_INCOMPLETE, PARSE_INCOMPLETE } from '@constants/status';
import type { ReactElement, FC } from 'react';
import type { ColumnDef, CellContext, HeaderGroup, Header, Row, Cell } from '@tanstack/react-table';
import type { QueriesState, SelectedQueryState, QueryCallback } from '@state/query';
import type { Query } from '@appTypes/query';

export interface QueryTableProps {
  columns?: Array<ColumnDef<Query>>;
}

export type PageItem = {
  value: number;
  active: boolean;
};

export type PageItems = {
  pages: Array<PageItem>;
  showEllipsis: boolean;
};

export function QueryTable({ columns }: QueryTableProps): ReactElement<FC> {
  const set = useSelectedQuery((state: SelectedQueryState): QueryCallback => state.set);
  const queries = useQueries((state: QueriesState): Array<Query> => state.queries);
  const queryTableColumnDefinitions = useMemo((): Array<ColumnDef<Query>> => ([
    {
      accessorKey: 'platform',
      header: 'Platform',
      cell: ({ row }: CellContext<Query, unknown>): ReactElement<FC> => (
        <span className="capitalize">{row.getValue('platform')}</span>
      )
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }: CellContext<Query, unknown>): ReactElement<FC> => {
        const status: string = row.getValue('status');
        const badgeClasses: string = cn({
          'bg-green-600/10 text-green-600': status === QUERY_COMPLETE,
          'bg-red-600/10 text-red-600': status === FETCH_INCOMPLETE || status === CLEAN_INCOMPLETE || status === PARSE_INCOMPLETE,
          'bg-zinc-600/10 text-zinc-600': status !== QUERY_COMPLETE && status !== FETCH_INCOMPLETE && status !== CLEAN_INCOMPLETE && status !== PARSE_INCOMPLETE,
        }, 'min-w-5 h-5 border-0 rounded-full font-bold tabular-nums');

        return <Badge className={badgeClasses}>{status}</Badge>;
      }
    },
    {
      accessorKey: 'createdAt',
      header: 'Date',
      cell: ({ row }: CellContext<Query, unknown>): ReactElement<FC> => {
        const date = new Date(row.getValue('createdAt'));

        return <span className="capitalize">{format(date, 'yyyy/MM/dd')}</span>;
      }
    },
    {
      accessorKey: 'percentage',
      header: 'Completed %',
      cell: ({ row }: CellContext<Query, unknown>): ReactElement<FC> => (
        <span className="capitalize">{`${Math.round((row.getValue('percentage') as number) * 100)}%`}</span>
      )
    },
    {
      id: 'query-toggle',
      cell: ({ row }: CellContext<Query, unknown>): ReactElement<FC> => (
        <Button
          variant="secondary"
          className="cursor-pointer"
          onClick={(): void => set(row.original)}>
          Details
        </Button>
      )
    }
  ]), []);
  const table = useReactTable({
    data: queries,
    columns: columns != null ? columns : queryTableColumnDefinitions,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });
  const paginationItems = useMemo((): PageItems => {
    const pageCount: number = table.getPageCount();

    if (pageCount <= 1) return {
      pages: [{ value: 0, active: true }],
      showEllipsis: false
    };

    const pages: Array<PageItem> = [];
    const pageIndex: number = table.getState().pagination.pageIndex;
    const maxVisible: number = 3;
    let start: number = pageIndex;
    let end: number = pageIndex + maxVisible;

    if (end > pageCount) {
      end = pageCount;
      start = Math.max(0, end - maxVisible);
    }

    for (let index: number = start; index < end; index++) {
      pages.push({
        value: index,
        active: index === pageIndex
      });
    }

    return {
      pages,
      showEllipsis: end < pageCount
    };
  }, [table.getState().pagination.pageIndex, table.getPageCount()]);

  useEffect((): void => {
    table.setPageSize(5);
  }, []);

  return (
    <Card className="col-span-8">
      <CardHeader>
        <CardTitle>Past Extractions</CardTitle>
        <CardDescription>
          Export complete requests, or finish and export the remainder of partially-complete requests
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden border rounded-md">
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((headerGroup: HeaderGroup<Query>): ReactElement<FC> => (
                <TableRow key={headerGroup.id}>
                  {headerGroup.headers.map((header: Header<Query, unknown>): ReactElement<FC> => (
                    <TableHead key={header.id}>
                      {header.isPlaceholder ? null : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows?.length > 0 && table.getRowModel().rows.map((row: Row<Query>): ReactElement<FC> => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell: Cell<Query, unknown>): ReactElement<FC> => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
      <CardFooter className="justify-center space-x-2 py-4">
        <Button
          variant="link"
          size="sm"
          className="cursor-pointer"
          onClick={() => table.previousPage()}
          disabled={!table.getCanPreviousPage()}
        >
          <ChevronLeft />
          Previous
        </Button>
        <ul className="flex flex-row">
          {paginationItems.pages.map((item: PageItem): ReactElement<FC> => (
            <li key={`${item.value}`}>
              <Button
                className="cursor-pointer"
                size="sm"
                variant={item.active ? 'outline' : 'link'}
                onClick={(): void => table.setPageIndex(item.value)}>
                {item.value + 1}
              </Button>
            </li>
          ))}
          {paginationItems.showEllipsis && (
            <li key={`${paginationItems.pages.length}`}>
              <Button variant="ghost" disabled>...</Button>
            </li>
          )}
        </ul>
        <Button
          variant="link"
          size="sm"
          className="cursor-pointer"
          onClick={() => table.nextPage()}
          disabled={!table.getCanNextPage()}
        >
          Next
          <ChevronRight />
        </Button>
      </CardFooter>
    </Card>
  );
}
