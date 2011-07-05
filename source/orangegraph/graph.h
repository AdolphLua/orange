#ifndef GRAPH_H
#define GRAPH_H

#include <QtGui/QGraphicsView>

class PlotItem;

class Graph : public QGraphicsView
{
    Q_OBJECT
public:
    Graph(QWidget* parent = 0);
    virtual ~Graph();
    
    void addItem(PlotItem* item);
    void removeItem(PlotItem* item);
    
    QRectF dataRectForAxes(int xAxis, int yAxis);
    QPair< double, double > boundsForAxis(int axis);
    
    QList<PlotItem*> itemList();
    
    QGraphicsRectItem* graph_item;
    
    void setDirty();
    
protected:
    void setClean();;
    bool isDirty();
    
private:
    QList<PlotItem*> m_items;
    bool m_dirty;
};

#endif // GRAPH_H
