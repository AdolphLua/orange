#include "networkcurve.h"

#include <QtCore/QMap>
#include <QtCore/QList>

#include <QtCore/qmath.h>

NodeItem::NodeItem(int index, int symbol, QColor color, int size, QGraphicsItem* parent): Point(symbol, color, size, parent)
{
    set_index(index);
}

NodeItem::~NodeItem()
{

}

void NodeItem::set_index(int index)
{
    m_index = index;
}

int NodeItem::index() const
{
    return m_index;
}

void NodeItem::set_graph_transform(const QTransform& transform)
{
    m_graph_transform = transform;
    set_coordinates(m_x, m_y);
}

QTransform NodeItem::graph_transform() const
{
    return m_graph_transform;
}

void NodeItem::set_x(double x)
{
    set_coordinates(x, m_y);
}

void NodeItem::set_y(double y)
{
    set_coordinates(m_x, y);
}

void NodeItem::set_coordinates(double x, double y)
{
    m_x = x;
    m_y = y;
    setPos(QPointF(m_x, m_y) * m_graph_transform);
}

double NodeItem::x() const
{
    return m_x;
}

double NodeItem::y() const
{
    return m_y;
}

void NodeItem::set_label(const QString& label)
{
    m_label = label;
}

QString NodeItem::label() const
{
    return m_label;
}

void NodeItem::set_tooltip(const QString& tooltip)
{
    setToolTip(tooltip);
}

void NodeItem::set_uuid(int uuid)
{
    m_uuid = uuid;
}

int NodeItem::uuid() const
{
    return m_uuid;
}

void NodeItem::add_connected_edge(EdgeItem* edge)
{
    m_connected_edges << edge;
}

void NodeItem::remove_connected_edge(EdgeItem* edge)
{
    m_connected_edges.removeAll(edge);
}

EdgeItem::EdgeItem(NodeItem* u, NodeItem* v, QGraphicsItem* parent, QGraphicsScene* scene): QGraphicsLineItem(parent, scene)
{
    set_u(u);
    set_v(v);
    m_size = 1;
    QPen p = pen();
	p.setWidthF(m_size);
	setPen(p);
}

EdgeItem::~EdgeItem()
{

}

void EdgeItem::set_u(NodeItem* item)
{
    m_u = item;
}

NodeItem* EdgeItem::u()
{
    return m_u;
}

void EdgeItem::set_v(NodeItem* item)
{
    m_v = item;
}

NodeItem* EdgeItem::v()
{
    return m_v;
}

void EdgeItem::set_tooltip(const QString& tooltip)
{
    setToolTip(tooltip);
}

void EdgeItem::set_label(const QString& label)
{
    m_label = label;
}

QString EdgeItem::label() const
{
    return m_label;
}

void EdgeItem::set_links_index(int index)
{
    m_links_index = index;
}

int EdgeItem::links_index() const
{
    return m_links_index;
}

void EdgeItem::set_arrow(EdgeItem::Arrow arrow, bool enable)
{
    if (enable)
    {
        set_arrows(arrows() | arrow);
    }
    else
    {
        set_arrows(arrows() & ~arrow);
    }
}

EdgeItem::Arrows EdgeItem::arrows()
{
    return m_arrows;
}

void EdgeItem::set_arrows(EdgeItem::Arrows arrows)
{
    m_arrows = arrows;
    // TODO: Update the QGraphicsItem element, add arrows
}

void EdgeItem::set_weight(double weight)
{
    m_weight = weight;
}

double EdgeItem::weight() const
{
    return m_weight;
}

NetworkCurve::NetworkCurve(QGraphicsItem* parent, QGraphicsScene* scene): Curve(parent, scene)
{

}

NetworkCurve::~NetworkCurve()
{

}

void NetworkCurve::update_properties()
{
    const QTransform t = graph_transform();

    update_items(m_nodes, NodeUpdater(t), UpdatePosition);
    update_items(m_edges, EdgeUpdater(t), UpdatePen);
}

QRectF NetworkCurve::data_rect() const
{
    QRectF r;
    bool first = true;
    foreach (const NodeItem* node, m_nodes)
    {
        if (first)
        {
            r = QRectF(node->x(), node->y(), 0, 0);
            first = false;
        }
        else
        {
            r.setTop( qMin(r.top(), node->y()) );
            r.setBottom( qMax(r.bottom(), node->y()) );
            r.setLeft( qMin(r.left(), node->x()) );
            r.setRight( qMax(r.right(), node->x()) );
        }
    }
    qDebug() << "NetworkCurve::dataRect()" << r;
    return r;
}

int NetworkCurve::random()
{
	NodeItem *u;
	Nodes::ConstIterator uit = m_nodes.constBegin();
	Nodes::ConstIterator uend = m_nodes.constEnd();

	for (; uit != uend; ++uit)
	{
		u = uit.value();
		u->set_x(((qreal)(qrand() % 1000)) * 1000);
		u->set_y(((qreal)(qrand() % 1000)) * 1000);
	}

	return 0;
}

int NetworkCurve::fr(int steps, bool weighted, double temperature, double cooling)
{
	int i, j;
	NodeItem *u, *v;
	EdgeItem *edge;
	QRectF data_r = data_rect();

	QMap<int, DataPoint> disp;
	foreach (const NodeItem* node, m_nodes)
	{
		DataPoint point;
		point.x = 0;
		point.y = 0;
		disp[node->index()] = point;
	}

	double area = data_r.width() * data_r.height();


	double k2 = area / m_nodes.size();
	double k = sqrt(k2);
	double kk = 2 * k;
	double kk2 = kk * kk;
	qDebug() << "area " << area << "; k2 " << k2 << "; k " << k << "; kk " << kk << "; kk2 " << kk2;
	// iterations
	for (i = 0; i < steps; i++)
	{
		foreach (const NodeItem* node, m_nodes)
		{
			disp[node->index()].x = 0;
			disp[node->index()].y = 0;
		}

		// calculate repulsive force
		Nodes::ConstIterator uit = m_nodes.constBegin();
		Nodes::ConstIterator uend = m_nodes.constEnd();
		for (; uit != uend; ++uit)
		{
			u = uit.value();
			Nodes::ConstIterator vit(uit);
			++vit;
			for (; vit != uend; ++vit)
			{
				v = vit.value();

				double difx = u->x() - v->x();
				double dify = u->y() - v->y();

				double dif2 = difx * difx + dify * dify;

				if (dif2 < kk2)
				{
					if (dif2 == 0)
						dif2 = 1;

					double dX = difx * k2 / dif2;
					double dY = dify * k2 / dif2;

					disp[u->index()].x += dX;
					disp[u->index()].y += dY;

					disp[v->index()].x -= dX;
					disp[v->index()].y -= dY;
				}
			}
		}

		// calculate attractive forces
		for (j = 0; j < m_edges.size(); ++j)
		{
			edge = m_edges[j];
			double difx = edge->u()->x() - edge->v()->x();
			double dify = edge->u()->y() - edge->v()->y();

			double dif = sqrt(difx * difx + dify * dify);

			double dX = difx * dif / k;
			double dY = dify * dif / k;

			if (weighted) {
				dX *= edge->weight();
				dY *= edge->weight();
			}

			disp[edge->u()->index()].x -= dX;
			disp[edge->u()->index()].y -= dY;

			disp[edge->v()->index()].x += dX;
			disp[edge->v()->index()].y += dY;
		}

		// limit the maximum displacement to the temperature t
		// and then prevent from being displaced outside frame
		Nodes::Iterator nit = m_nodes.begin();
		for (; nit != m_nodes.end(); ++nit)
		{
			u = nit.value();
			double dif = sqrt(disp[u->index()].x * disp[u->index()].x + disp[u->index()].y * disp[u->index()].y);

			if (dif == 0)
				dif = 1;

			u->set_x(u->x() + (disp[u->index()].x * qMin(fabs(disp[u->index()].x), temperature) / dif));
			u->set_y(u->y() + (disp[u->index()].y * qMin(fabs(disp[u->index()].y), temperature) / dif));
		}

		plot()->replot();
		plot()->set_dirty();

		temperature = temperature * cooling;
	}

	return 0;
}

void NetworkCurve::set_edges(NetworkCurve::Edges edges)
{
    qDeleteAll(m_edges);
    m_edges = edges;
}

void NetworkCurve::set_nodes(NetworkCurve::Nodes nodes)
{
    qDeleteAll(m_nodes);
    m_nodes = nodes;
}


