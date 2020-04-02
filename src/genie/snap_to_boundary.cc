class ObservePointData {
public:
	/// Constructor
	ObservePointData()
	: distance_(numeric_limits<double>::infinity()) {};

	/// Final element of the observe point. The index in the mesh.
	unsigned int element_idx_;

	/// Global coordinates of the observation point.
	arma::vec3 global_coords_;

	/// Local (barycentric) coordinates on the element.
	arma::vec local_coords_;

	/// Distance of found projection from the initial point.
	/// If we find more candidates we pass in the closest one.
	double distance_;

	/// Actual process of the observe point.
	unsigned int proc_;

	/// Global index of the observe point.
	LongIdx global_idx_;

	/// Local index on actual process of the observe point.
	LongIdx local_idx_;
};


template<unsigned int dim, unsigned int spacedim>
auto MappingP1<dim,spacedim>::element_map(ElementAccessor<3> elm) -> ElementMap
{
    ElementMap coords;
    for (unsigned int i=0; i<dim+1; i++)
        coords.col(i) = *elm.node(i);
    return coords;
}

template<unsigned int dim, unsigned int spacedim>
auto MappingP1<dim,spacedim>::project_real_to_unit(const RealPoint &point, const ElementMap &map) -> BaryPoint
{
    arma::mat::fixed<3, dim> A = map.cols(1,dim);
    for(unsigned int i=0; i < dim; i++ ) {
        A.col(i) -= map.col(0);
    }
    
    arma::mat::fixed<dim, dim> AtA = A.t()*A;
    arma::vec::fixed<dim> Atb = A.t()*(point - map.col(0));
    arma::vec::fixed<dim+1> bary_coord;
    bary_coord.rows(1, dim) = arma::solve(AtA, Atb);
    bary_coord( 0 ) = 1.0 - arma::sum( bary_coord.rows(1,dim) );
    return bary_coord;
}

template<unsigned int dim, unsigned int spacedim>
auto MappingP1<dim,spacedim>::clip_to_element(BaryPoint &barycentric) -> BaryPoint{
    return RefElement<dim>::clip(barycentric);
}


template<unsigned int dim>
auto RefElement<dim>::clip(const BaryPoint &barycentric) -> BaryPoint
{
    static BarycentricUnitVec bary_unit_vec = make_bary_unit_vec();
    ASSERT_EQ_DBG(barycentric.n_rows, dim+1);
    for(unsigned int i_bary=0; i_bary < dim +1; i_bary ++) {
        if (barycentric[i_bary] < 0.0) {
            // index of barycentric coord that is constant on the face i_side
            // as we use barycentric coords starting with local coordinates:
            // TODO: rather work only with local coords and/or with canonical barycentric coords
            unsigned int i_side = (dim - i_bary);
            // project to face
            arma::vec projection_to_face(dim+1);
            //barycentric.print(cout, "input");
            //cout << "is: " << i_side << endl;
            //cout << "ibary: " << i_bary << endl;
            //bary_unit_vec[i_bary].print(cout, "normal");
            //barycentric.subvec(0, dim-1).print(cout, "bary sub");
            projection_to_face = barycentric - barycentric[i_bary]*bary_unit_vec[i_bary];
            //projection_to_face(dim) = 1.0 - arma::sum(projection_to_face.subvec(0, dim-1));
            //projection_to_face.print(cout, "projection");
            auto bary_on_face = barycentric_on_face(projection_to_face, i_side);
            //bary_on_face.print(cout, "b on f");
            auto sub_clip = RefElement<dim-1>::clip(bary_on_face);
            //sub_clip.print(cout, "sub clip");
            return interpolate<dim-1>(sub_clip, i_side);
        }
    }
    return barycentric;

}


template<unsigned int dim>
class ProjectionHandler {
public:
	/// Constructor
	ProjectionHandler() {};

	ObservePointData projection(arma::vec3 input_point, unsigned int i_elm, ElementAccessor<3> elm) {
		arma::mat::fixed<3, dim+1> elm_map = MappingP1<dim,3>::element_map(elm);
                
		arma::vec::fixed<dim+1> projection = MappingP1<dim,3>::project_real_to_unit(input_point, elm_map);
                
		projection = MappingP1<dim,3>::clip_to_element(projection);

		ObservePointData data;
		data.element_idx_ = i_elm;
		data.local_coords_ = projection.rows(1, elm.dim());
		data.global_coords_ = elm_map*projection;
		data.distance_ = arma::norm(data.global_coords_ - input_point, 2);
		data.proc_ = elm.proc();

		return data;
	}

//     /**
//      * Snap local coords to the subelement. Called by the ObservePoint::snap method.
//      */
// 	void snap_to_subelement(ObservePointData & observe_data, ElementAccessor<3> elm, unsigned int snap_dim)
// 	{
// 		if (snap_dim <= dim) {
// 			double min_dist = 2.0; // on the ref element the max distance should be about 1.0, smaler then 2.0
// 			arma::vec min_center;
// 			for(auto &center : RefElement<dim>::centers_of_subelements(snap_dim))
// 			{
// 				double dist = arma::norm(center - observe_data.local_coords_, 2);
// 				if ( dist < min_dist) {
// 					min_dist = dist;
// 					min_center = center;
// 				}
// 			}
// 			observe_data.local_coords_ = min_center;
// 		}
// 
// 		arma::mat::fixed<3, dim+1> elm_map = MappingP1<dim,3>::element_map(elm);
//         observe_data.global_coords_ =  elm_map * RefElement<dim>::local_to_bary(observe_data.local_coords_);
// 	}

};

template class ProjectionHandler<1>;
template class ProjectionHandler<2>;
template class ProjectionHandler<3>;


/**
 * Helper struct, used as comparator of priority queue in ObservePoint::find_observe_point.
 */
struct CompareByDist
{
  bool operator()(const ObservePointData& lhs, const ObservePointData& rhs) const
  {
    return lhs.distance_ > rhs.distance_;
  }
};


ObservePointData ObservePoint::point_projection(unsigned int i_elm, ElementAccessor<3> elm) {
	switch (elm.dim()) {
// 	case 1:
// 	{
// 		ProjectionHandler<1> ph;
// 		return ph.projection(input_point_, i_elm, elm);
// 		break;
// 	}
	case 2:
	{
		ProjectionHandler<2> ph;
		return ph.projection(input_point_, i_elm, elm);
		break;
	}
// 	case 3:
// 	{
// 		ProjectionHandler<3> ph;
// 		return ph.projection(input_point_, i_elm, elm);
// 		break;
// 	}
// 	default:
// 		ASSERT(false).error("Invalid element dimension!");
// 	}
// 
	return ObservePointData(); // Should not happen.
}



void ObservePoint::find_observe_point(Mesh &mesh) {
    RegionSet region_set = mesh.region_db().get_region_set(snap_region_name_);
    if (region_set.size() == 0)
        THROW( RegionDB::ExcUnknownSet() << RegionDB::EI_Label(snap_region_name_) << in_rec_.ei_address() );


    const BIHTree &bih_tree=mesh.get_bih_tree();
    vector<unsigned int> candidate_list;
    std::unordered_set<unsigned int> closed_elements(1023);
    std::priority_queue< ObservePointData, std::vector<ObservePointData>, CompareByDist > candidate_queue;

    // search for the initial element
    auto projected_point = bih_tree.tree_box().project_point(input_point_);
    bih_tree.find_point(projected_point, candidate_list, true);

    // closest element
    ObservePointData min_observe_point_data;
    
    for (unsigned int i_candidate=0; i_candidate<candidate_list.size(); ++i_candidate) {
        unsigned int i_elm=candidate_list[i_candidate];
        ElementAccessor<3> elm = mesh.element_accessor(i_elm);

        // project point, add candidate to queue
        auto observe_data = point_projection( i_elm, elm );
          
        // Here we have projected point.

        // save the closest element for later diagnostic
        if(observe_data.distance_ < min_observe_point_data.distance_)
            min_observe_point_data = observe_data;
//         
//         // queue only the elements in the maximal search radius
//         if (observe_data.distance_ <= max_search_radius_)
//         	candidate_queue.push(observe_data);
//         closed_elements.insert(i_elm);
    }

//     // no candidates found -> exception
//     if (candidate_queue.empty()) {
//         THROW(ExcNoObserveElementCandidates()
//             << EI_PointName(name_)
//             << EI_Point(input_point_)
//             << EI_ClosestEle(min_observe_point_data));
//     }
//     
//     while (!candidate_queue.empty())
//     {
//         auto candidate_data = candidate_queue.top();
//         candidate_queue.pop();
// 
//         unsigned int i_elm=candidate_data.element_idx_;
//         ElementAccessor<3> elm = mesh.element_accessor(i_elm);
// 
//         // test if candidate is in region and update projection
//         if (elm.region().is_in_region_set(region_set)) {
//             ASSERT_LE(candidate_data.distance_, observe_data_.distance_).error();
// 
// 			observe_data_.distance_ = candidate_data.distance_;
// 			observe_data_.element_idx_ = candidate_data.element_idx_;
// 			observe_data_.local_coords_ = candidate_data.local_coords_;
// 			observe_data_.global_coords_ = candidate_data.global_coords_;
// 			observe_data_.proc_ = candidate_data.proc_;
//             break;
//         }
// 
//         // add candidates to queue
// 		for (unsigned int n=0; n < elm->n_nodes(); n++)
// 			for(unsigned int i_node_ele : mesh.node_elements()[elm.node(n).idx()]) {
// 				if (closed_elements.find(i_node_ele) == closed_elements.end()) {
// 					ElementAccessor<3> neighbor_elm = mesh.element_accessor(i_node_ele);
// 					auto observe_data = point_projection( i_node_ele, neighbor_elm );
// 			        if (observe_data.distance_ <= max_search_radius_)
// 			        	candidate_queue.push(observe_data);
// 			        closed_elements.insert(i_node_ele);
// 				}
// 			}
//     }
// 
//     if (! have_observe_element()) {
//         THROW(ExcNoObserveElement()
//             << EI_RegionName(snap_region_name_)
//             << EI_PointName(name_)
//             << EI_Point(input_point_)
//             << EI_ClosestEle(min_observe_point_data));
//     }
//     snap( mesh );
//     ElementAccessor<3> elm = mesh.element_accessor(observe_data_.element_idx_);
//     double dist = arma::norm(elm.centre() - input_point_, 2);
//     double elm_norm = arma::norm(elm.bounding_box().max() - elm.bounding_box().min(), 2);
//     if (dist > 2*elm_norm)
//     	WarningOut().fmt("Observe point ({}) is too distant from the mesh.\n", name_);
}
