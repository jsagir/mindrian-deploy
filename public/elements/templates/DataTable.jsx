/**
 * DataTable - Template for sortable data tables with row actions
 *
 * Copy to: public/elements/YourTableName.jsx
 * Usage: cl.CustomElement(name="YourTableName", props={...})
 *
 * Props:
 * - title: string (optional)
 * - columns: array of {key, label, type?}
 * - rows: array of objects
 * - sortable: boolean
 */

import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowUp, ArrowDown, ExternalLink, MoreHorizontal } from "lucide-react"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { useState } from "react"

export default function DataTable() {
  // === CHAINLIT API ACCESS ===
  const { updateElement, callAction, sendUserMessage } = window.Chainlit || {}

  // Props are global
  const {
    title = "",
    columns = [],
    rows = [],
    sortable = true,
    rowActions = [],
    element_id = null
  } = props || {}

  // === LOCAL STATE ===
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })

  // === SORTING ===
  const sortedRows = [...rows].sort((a, b) => {
    if (!sortConfig.key) return 0
    const aVal = a[sortConfig.key]
    const bVal = b[sortConfig.key]
    if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1
    if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1
    return 0
  })

  const handleSort = (key) => {
    if (!sortable) return
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }))
  }

  // === HANDLERS ===
  const handleRowClick = (row) => {
    if (callAction) {
      callAction({ name: "row_selected", payload: { row } })
    }
  }

  const handleRowAction = (actionName, row) => {
    if (callAction) {
      callAction({ name: actionName, payload: { row } })
    }
  }

  // === CELL RENDERER ===
  const renderCell = (row, col) => {
    const value = row[col.key]

    switch (col.type) {
      case 'badge':
        return <Badge variant="outline">{value}</Badge>

      case 'status':
        const statusColors = {
          active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
          pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
          inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
          error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
        }
        return (
          <Badge className={statusColors[value?.toLowerCase()] || ''}>
            {value}
          </Badge>
        )

      case 'link':
        return (
          <a
            href={value}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline flex items-center gap-1"
          >
            Link <ExternalLink className="h-3 w-3" />
          </a>
        )

      case 'currency':
        return typeof value === 'number'
          ? `$${value.toLocaleString()}`
          : value

      case 'date':
        try {
          return new Date(value).toLocaleDateString()
        } catch {
          return value
        }

      default:
        return value
    }
  }

  // === RENDER ===
  return (
    <div className="w-full border rounded-lg overflow-hidden">
      {title && (
        <div className="px-4 py-3 bg-muted/50 border-b">
          <h3 className="font-semibold">{title}</h3>
        </div>
      )}

      <Table>
        <TableHeader>
          <TableRow>
            {columns.map(col => (
              <TableHead
                key={col.key}
                className={sortable ? "cursor-pointer hover:bg-muted/50 select-none" : ""}
                onClick={() => handleSort(col.key)}
              >
                <div className="flex items-center gap-1">
                  {col.label}
                  {sortConfig.key === col.key && (
                    sortConfig.direction === 'asc'
                      ? <ArrowUp className="h-3 w-3" />
                      : <ArrowDown className="h-3 w-3" />
                  )}
                </div>
              </TableHead>
            ))}
            {rowActions.length > 0 && (
              <TableHead className="w-12"></TableHead>
            )}
          </TableRow>
        </TableHeader>

        <TableBody>
          {sortedRows.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={columns.length + (rowActions.length > 0 ? 1 : 0)}
                className="text-center text-muted-foreground py-8"
              >
                No data available
              </TableCell>
            </TableRow>
          ) : (
            sortedRows.map((row, i) => (
              <TableRow
                key={row.id || i}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => handleRowClick(row)}
              >
                {columns.map(col => (
                  <TableCell key={col.key}>
                    {renderCell(row, col)}
                  </TableCell>
                ))}
                {rowActions.length > 0 && (
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        {rowActions.map((action, idx) => (
                          <DropdownMenuItem
                            key={idx}
                            onClick={(e) => {
                              e.stopPropagation()
                              handleRowAction(action.name, row)
                            }}
                            className={action.destructive ? 'text-destructive' : ''}
                          >
                            {action.label}
                          </DropdownMenuItem>
                        ))}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </TableCell>
                )}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}

/*
================================================================================
PYTHON USAGE EXAMPLE
================================================================================

import chainlit as cl

@cl.on_message
async def main(message: cl.Message):
    elements = [
        cl.CustomElement(
            name="DataTable",
            props={
                "title": "Recent Orders",
                "sortable": True,
                "columns": [
                    {"key": "id", "label": "Order ID"},
                    {"key": "customer", "label": "Customer"},
                    {"key": "amount", "label": "Amount", "type": "currency"},
                    {"key": "status", "label": "Status", "type": "status"},
                    {"key": "date", "label": "Date", "type": "date"}
                ],
                "rows": [
                    {"id": "ORD-001", "customer": "Acme Corp", "amount": 1250, "status": "Active", "date": "2026-01-28"},
                    {"id": "ORD-002", "customer": "TechStart", "amount": 890, "status": "Pending", "date": "2026-01-29"},
                    {"id": "ORD-003", "customer": "GlobalInc", "amount": 2100, "status": "Active", "date": "2026-01-30"}
                ],
                "rowActions": [
                    {"label": "View Details", "name": "view_order"},
                    {"label": "Edit", "name": "edit_order"},
                    {"label": "Delete", "name": "delete_order", "destructive": True}
                ]
            },
            display="inline"
        )
    ]
    await cl.Message(content="Here are your orders:", elements=elements).send()

@cl.action_callback("row_selected")
async def handle_row(action: cl.Action):
    row = action.payload.get("row")
    await cl.Message(content=f"Selected: {row.get('id')}").send()

@cl.action_callback("view_order")
async def handle_view(action: cl.Action):
    row = action.payload.get("row")
    await cl.Message(content=f"Viewing order: {row.get('id')}").send()

================================================================================
*/
