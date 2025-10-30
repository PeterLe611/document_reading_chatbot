import useSWR from 'swr';
import { baseURL } from '../stores/apiList';

// This function tells SWR how to fetch data
const fetcher = (url: string) => fetch(url).then(res => res.json());

function DocumentList() {
    // Use the SWR hook to fetch from your FastAPI backend
    const { data: documents, error } = useSWR(
        baseURL + 'documents', // Your API endpoint
        fetcher,
        { refreshInterval: 5000 } // <-- This polls for new data every 5 seconds
    );

    if (error) return <div>Failed to load documents </div>;
    if (!documents) return <div>Loading...</div>;

    return (
        <div>
        <h1>Document Monitor </h1>
            < table >
            <thead>
            <tr>
            <th>Name </th>
            <th> Status </th>
    {/* Add other columns as needed */ }
    </tr>
        </thead>
        <tbody>
    {
        documents.map((doc: any) => (
            <tr key= { doc.id } > {/* Make sure your payload has an id */ }
            < td > { doc.name } </td>
            < td > { doc.status } </td>
            </tr>
        ))
    }
    </tbody>
        </table>
        </div>
  );
}