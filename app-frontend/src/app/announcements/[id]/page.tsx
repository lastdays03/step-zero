import AnnouncementClient from './AnnouncementClient';

export default async function AnnouncementDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    return <AnnouncementClient idParam={id} />;
}
